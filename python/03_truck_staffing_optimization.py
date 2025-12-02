# 03_truck_staffing_optimization.py
# Recommend how many trucks to stage in each zone/hour using forecasts and a simple
# integer programming model.
#
# Uses:
#   - pandas
#   - SQLAlchemy
#   - pulp (linear/integer programming)
#
# This script:
#   1. Reads hourly forecasts from roadside_demand_forecast_hourly.
#   2. Uses a simple rule-of-thumb capacity per truck.
#   3. Minimizes total trucks subject to capacity constraints.
#   4. Writes recommendations into roadside_staffing_plan.

import os
import pandas as pd
from sqlalchemy import create_engine, text
import pulp

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
MYSQL_USER = os.getenv("AAA_DB_USER", "root")
MYSQL_PWD  = os.getenv("AAA_DB_PWD", "root")
MYSQL_HOST = os.getenv("AAA_DB_HOST", "localhost")
MYSQL_PORT = os.getenv("AAA_DB_PORT", "3306")
MYSQL_DB   = "aaa_roadside"

CONNECTION_STRING = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PWD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

# Simple capacity assumptions
CALLS_PER_TRUCK_PER_HOUR = 2.0   # how many calls one truck can handle per hour
TARGET_SERVICE_LEVEL      = 0.90  # cover 90% of forecasted demand
# --------------------------------------------------------------------


def get_engine():
    """Create a SQLAlchemy engine."""
    return create_engine(CONNECTION_STRING)


def load_forecast(engine):
    """
    Load hourly call forecasts from roadside_demand_forecast_hourly.

    Expected columns:
      - ts (DATETIME)
      - zone_id (INT)
      - forecast_calls (DOUBLE)
    """
    query = text("""
        SELECT
            ts,
            zone_id,
            forecast_calls
        FROM roadside_demand_forecast_hourly
        ORDER BY ts, zone_id;
    """)
    df = pd.read_sql(query, engine, parse_dates=["ts"])
    return df


def ensure_output_table(engine):
    """
    Ensure the staffing output table exists.
    One row per (ts, zone_id).
    """
    ddl = text("""
        CREATE TABLE IF NOT EXISTS roadside_staffing_plan (
            ts                DATETIME NOT NULL,
            zone_id           INT NOT NULL,
            num_trucks        INT,
            forecast_calls    DOUBLE,
            target_service_lvl DOUBLE,
            model_name        VARCHAR(50),
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (ts, zone_id)
        );
    """)
    with engine.begin() as conn:
        conn.execute(ddl)


def optimize_staffing(df,
                      calls_per_truck=CALLS_PER_TRUCK_PER_HOUR,
                      target_service_lvl=TARGET_SERVICE_LEVEL):
    """
    Build and solve an integer programming model to recommend trucks per zone/hour.

    Decision variable:
      x[z, t] = integer number of trucks in zone z at time t.

    Objective:
      Minimize total trucks across zones and hours.

    Constraint:
      x[z, t] * calls_per_truck >= forecast_calls[z, t] * target_service_lvl
    """
    if df.empty:
        return pd.DataFrame()

    # Work on a copy and normalize types
    df = df.copy()
    df["zone_id"] = df["zone_id"].astype(int)

    # Demand dictionary: keys are (zone_id:int, ts:Timestamp)
    demand = {
        (int(row.zone_id), row.ts): float(row.forecast_calls)
        for row in df.itertuples()
    }

    zones = sorted(int(z) for z in df["zone_id"].unique())
    times = sorted(df["ts"].unique())

    print(f"Zones in forecast: {zones}")

    # Define the optimization model
    model = pulp.LpProblem("Truck_Staffing", pulp.LpMinimize)

    # Decision variables: number of trucks for each (zone, time)
    x = {}
    for z in zones:
        for t in times:
            # Only create variables where we actually have demand key
            if (z, t) in demand:
                t_str = t.strftime("%Y%m%d%H")
                var_name = f"x_{z}_{t_str}"
                x[(z, t)] = pulp.LpVariable(var_name, lowBound=0, cat="Integer")

    if not x:
        # No variables → no demand / no forecast
        return pd.DataFrame()

    # Objective: minimize total number of trucks across all zones and times
    model += pulp.lpSum(x[(z, t)] for (z, t) in x), "Total_Trucks"

    # Constraints: each zone-hour must cover target % of demand
    for (z, t), var in x.items():
        fc = demand[(z, t)]
        required_calls = fc * target_service_lvl
        model += (
            var * calls_per_truck >= required_calls,
            f"DemandCoverage_z{z}_t{t.strftime('%Y%m%d%H')}"
        )

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)

    # Collect solution
    records = []
    for (z, t), var in x.items():
        trucks = var.varValue
        if trucks is None:
            trucks = 0
        trucks = int(round(trucks))

        fc = demand[(z, t)]

        records.append({
            "ts": t,
            "zone_id": int(z),
            "num_trucks": trucks,
            "forecast_calls": fc,
            "target_service_lvl": target_service_lvl,
        })

    staffing_df = pd.DataFrame(records).sort_values(["ts", "zone_id"])
    return staffing_df


def write_staffing_plan(engine, staffing_df, model_name_hint="HW_or_Naive"):
    """
    Persist the staffing recommendations to roadside_staffing_plan.
    Uses a simple delete-and-reinsert strategy for the forecast horizon.
    """
    if staffing_df.empty:
        return

    ensure_output_table(engine)

    # Attach model_name column
    out_df = staffing_df.copy()
    out_df["model_name"] = model_name_hint

    with engine.begin() as conn:
        # Delete any existing rows in this time range to avoid duplicates
        min_ts = out_df["ts"].min()
        max_ts = out_df["ts"].max()

        delete_sql = text("""
            DELETE FROM roadside_staffing_plan
            WHERE ts BETWEEN :min_ts AND :max_ts;
        """)
        conn.execute(delete_sql, {"min_ts": min_ts, "max_ts": max_ts})

        # Insert new results
        out_df.to_sql(
            "roadside_staffing_plan",
            conn,
            if_exists="append",
            index=False
        )


def main():
    engine = get_engine()
    df_forecast = load_forecast(engine)

    if df_forecast.empty:
        print("No forecast data found in roadside_demand_forecast_hourly.")
        return

    staffing_df = optimize_staffing(df_forecast)

    if staffing_df.empty:
        print("No staffing plan created.")
        return

    write_staffing_plan(engine, staffing_df, model_name_hint="HW_or_Naive")
    print("Staffing plan written to roadside_staffing_plan.")


if __name__ == "__main__":
    main()
