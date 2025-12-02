import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.cluster import DBSCAN

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

EPS_KM = 2.0      # clustering radius in kilometers
MIN_SAMPLES = 3   # minimum points per cluster
# ----------------------------------------------------------------------------


def get_engine():
    return create_engine(CONNECTION_STRING)


def load_points(engine):
    query = text("""
        SELECT
            request_id,
            latitude,
            longitude
        FROM roadside_requests
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL;
    """)
    return pd.read_sql(query, engine)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    dlat = lat2_rad - lat1_rad
    dlon = np.radians(lon2) - np.radians(lon1)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def assign_clusters(df):
    coords = df[["latitude", "longitude"]].to_numpy()
    if len(coords) < MIN_SAMPLES:
        df["cluster"] = -1
        return df

    def metric(u, v):
        return haversine_km(u[0], u[1], v[0], v[1])

    clustering = DBSCAN(
        eps=EPS_KM,
        min_samples=MIN_SAMPLES,
        metric=metric
    ).fit(coords)

    df = df.copy()
    df["cluster"] = clustering.labels_

    # Remap cluster labels to zone_ids:
    #   cluster >= 0 → zone_id = 1..K
    #   cluster = -1 → zone_id = 0 (noise / catch-all)
    unique_clusters = sorted(c for c in df["cluster"].unique() if c >= 0)
    cluster_to_zone = {cl: i + 1 for i, cl in enumerate(unique_clusters)}

    def to_zone_id(cluster_label):
        if cluster_label == -1:
            return 0
        return cluster_to_zone.get(cluster_label, 0)

    df["zone_id"] = df["cluster"].apply(to_zone_id)
    return df


def update_zone_ids(engine, df):
    """
    Update roadside_requests.zone_id from the dataframe.
    For your synthetic dataset (a few thousand rows), row-by-row UPDATE is fine.
    """
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text("""
                    UPDATE roadside_requests
                    SET zone_id = :zone_id
                    WHERE request_id = :request_id
                """),
                {
                    "zone_id": int(row["zone_id"]),
                    "request_id": int(row["request_id"])
                }
            )


def main():
    engine = get_engine()
    df = load_points(engine)
    if df.empty:
        print("No points with lat/long found.")
        return

    df = assign_clusters(df)

    # Quick sanity check: how many per zone?
    print(df["zone_id"].value_counts().sort_index())

    update_zone_ids(engine, df)
    print("zone_id updated in roadside_requests.")


if __name__ == "__main__":
    main()
