# 01_demand_forecast_time.py
# Multi-zone hourly demand forecasting for roadside requests.
#
# This script:
#   1. Connects to the aaa_roadside database.
#   2. Aggregates calls per hour *per zone*.
#   3. Fits a Holt-Winters model for EACH ZONE separately.
#   4. Writes per-zone forecasts to roadside_demand_forecast_hourly.

import os
import pandas as pd
from sqlalchemy import create_engine, text
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# --- CONFIG -----------------------------------------------------------------
MYSQL_USER = os.getenv("AAA_DB_USER", "root")
MYSQL_PWD  = os.getenv("AAA_DB_PWD", "root")
MYSQL_HOST = os.getenv("AAA_DB_HOST", "localhost")
MYSQL_PORT = os.getenv("AAA_DB_PORT", "3306")
MYSQL_DB   = "aaa_roadside"

CONNECTION_STRING = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PWD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

FORECAST_HORIZON_HOURS = 48
# ----------------------------------------------------------------------------


def get_engine():
    return create_engine(CONNECTION_STRING)


def load_hourly_counts(engine):
    """
    Returns hourly call counts PER ZONE:
       ts_hour, zone_id, call_count
    """
    query = text("""
        SELECT
            DATE_FORMAT(request_ts, '%Y-%m-%d %H:00:00') AS ts_hour,
            zone_id,
            COUNT(*) AS call_count
        FROM roadside_requests
        WHERE zone_id IS NOT NULL
        GROUP BY DATE_FORMAT(request_ts, '%Y-%m-%d %H:00:00'), zone_id
        ORDER BY ts_hour, zone_id;
    """)
    df = pd.read_sql(query, engine, parse_dates=["ts_hour"])
    return df


def ensure_output_table(engine):
    ddl = text("""
        CREATE TABLE IF NOT EXISTS roadside_demand_forecast_hourly (
            ts               DATETIME NOT NULL,
            zone_id          INT NOT NULL,
            forecast_calls   DOUBLE,
            lower_80         DOUBLE,
            upper_80         DOUBLE,
            model_name       VARCHAR(50),
            created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ts, zone_id)
        );
    """)
    with engine.begin() as conn:
        conn.execute(ddl)


def forecast_series(series, horizon=FORECAST_HORIZON_HOURS):
    """
    Holt-Winters additive weekly model.
    Falls back to naive forecast if HW fails.
    """
    if len(series) < 24:
        # Too little data → naive
        mean_val = series.mean()
        idx = pd.date_range(series.index[-1] + pd.Timedelta(hours=1),
                            periods=horizon, freq="H")
        forecast = pd.Series([mean_val] * horizon, index=idx)
        return forecast, forecast * 0.8, forecast * 1.2, "NaiveMean"

    try:
        hw = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=24 * 7
        ).fit()

        forecast = hw.forecast(horizon)
        residuals = series - hw.fittedvalues
        sigma = residuals.std() if len(residuals) > 1 else 1.0

        lower_80 = forecast - 1.28 * sigma
        upper_80 = forecast + 1.28 * sigma
        return forecast, lower_80, upper_80, "HW_Additive_Weekly"

    except Exception as e:
        print(f"HW failed, using naive for zone: {e}")
        mean_val = series.mean()
        idx = pd.date_range(series.index[-1] + pd.Timedelta(hours=1),
                            periods=horizon, freq="H")
        forecast = pd.Series([mean_val] * horizon, index=idx)
        return forecast, forecast * 0.8, forecast * 1.2, "NaiveMean"


def write_forecasts(engine, df):
    """
    Writes MULTI-ZONE forecasts.
    Each zone is forecast separately.
    """
    ensure_output_table(engine)

    records = []

    # Group dataset by zone_id
    for zone_id, df_zone in df.groupby("zone_id"):
        # Make a continuous hourly index for this zone
        df_zone = df_zone.set_index("ts_hour").asfreq("H").fillna(0)
        series = df_zone["call_count"]

        forecast, lower_80, upper_80, model_name = forecast_series(series)

        for ts in forecast.index:
            records.append({
                "ts": ts,
                "zone_id": int(zone_id),
                "forecast_calls": float(forecast.loc[ts]),
                "lower_80": float(lower_80.loc[ts]),
                "upper_80": float(upper_80.loc[ts]),
                "model_name": model_name
            })

    out_df = pd.DataFrame(records)

    # Write output
    with engine.begin() as conn:
        if not out_df.empty:
            min_ts = out_df["ts"].min()
            max_ts = out_df["ts"].max()

            conn.execute(
                text("""
                    DELETE FROM roadside_demand_forecast_hourly
                    WHERE ts BETWEEN :min_ts AND :max_ts;
                """),
                {"min_ts": min_ts, "max_ts": max_ts}
            )

            out_df.to_sql(
                "roadside_demand_forecast_hourly",
                conn,
                if_exists="append",
                index=False
            )


def main():
    engine = get_engine()
    df = load_hourly_counts(engine)

    if df.empty:
        print("No data found in roadside_requests.")
        return

    print("Zones found:", sorted(df["zone_id"].unique()))
    write_forecasts(engine, df)
    print("Multi-zone forecasts written.")


if __name__ == "__main__":
    main()
