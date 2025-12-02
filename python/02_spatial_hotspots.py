# 02_spatial_hotspots.py
# Identify spatial hotspots of roadside calls using clustering.
#
# This script:
#   1. Connects to the aaa_roadside database.
#   2. Pulls lat/long for all calls (single region).
#   3. Runs DBSCAN to find clusters (hotspots) across the territory.
#   4. Writes cluster centroids and a simple hotspot score into roadside_hotspots.
#
# For now, we treat the entire service area as a single zone with zone_id = 0.
# The schema is ready to be extended to multiple zones in the future.

import os
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.cluster import DBSCAN
import numpy as np

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

# DBSCAN parameters: tune these based on your geography
EPS_KM = 2.0   # approx. radius in kilometers
MIN_SAMPLES = 3
# ----------------------------------------------------------------------------


def get_engine():
    return create_engine(CONNECTION_STRING)


def load_points(engine):
    """
    Load point-level roadside request data with lat/long.
    We no longer assume a zone_id column in roadside_requests.
    """
    query = text("""
        SELECT
            request_id,
            request_ts,
            latitude,
            longitude
        FROM roadside_requests
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL;
    """)
    df = pd.read_sql(query, engine, parse_dates=["request_ts"])
    return df


def ensure_output_table(engine):
    """
    Ensure the roadside_hotspots table exists.
    We still include zone_id for future multi-zone support;
    for now, we always use zone_id = 0 (entire territory).
    """
    ddl = text("""
        CREATE TABLE IF NOT EXISTS roadside_hotspots (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            as_of_date      DATE NOT NULL,
            zone_id         INT NOT NULL,
            cluster_id      INT NOT NULL,
            centroid_lat    DOUBLE,
            centroid_lng    DOUBLE,
            hotspot_score   DOUBLE,
            method          VARCHAR(50),
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    with engine.begin() as conn:
        conn.execute(ddl)


def haversine_km(lat1, lon1, lat2, lon2):
    # Vectorized haversine distance in kilometers
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


def dbscan_for_zone(df_zone):
    """
    Run DBSCAN for a single group of points (here: whole territory).
    """
    coords = df_zone[["latitude", "longitude"]].to_numpy()
    if len(coords) < MIN_SAMPLES:
        df_zone["cluster"] = -1
        return df_zone

    def metric(u, v):
        return haversine_km(u[0], u[1], v[0], v[1])

    clustering = DBSCAN(
        eps=EPS_KM,
        min_samples=MIN_SAMPLES,
        metric=metric
    ).fit(coords)

    df_zone = df_zone.copy()
    df_zone["cluster"] = clustering.labels_
    return df_zone


def compute_hotspots(df):
    """
    Compute hotspots for the entire region (single zone).
    We treat everything as zone_id = 0.
    """
    df = dbscan_for_zone(df)

    results = []
    for cluster_id, df_cluster in df.groupby("cluster"):
        if cluster_id == -1:
            continue  # noise, skip

        centroid_lat = df_cluster["latitude"].mean()
        centroid_lng = df_cluster["longitude"].mean()
        hotspot_score = len(df_cluster)  # simple: number of calls in cluster

        results.append({
            "as_of_date": df_cluster["request_ts"].max().date(),
            "zone_id": 0,  # single global zone
            "cluster_id": int(cluster_id),
            "centroid_lat": float(centroid_lat),
            "centroid_lng": float(centroid_lng),
            "hotspot_score": float(hotspot_score),
            "method": "DBSCAN_haversine"
        })

    return pd.DataFrame(results)


def write_hotspots(engine, hotspots_df):
    ensure_output_table(engine)
    if hotspots_df.empty:
        print("No hotspots identified.")
        return

    with engine.begin() as conn:
        # Simple approach: append results
        hotspots_df.to_sql(
            "roadside_hotspots",
            conn,
            if_exists="append",
            index=False
        )


def main():
    engine = get_engine()
    df = load_points(engine)
    if df.empty:
        print("No lat/long data found in roadside_requests.")
        return

    hotspots_df = compute_hotspots(df)
    write_hotspots(engine, hotspots_df)
    print("Hotspots written to roadside_hotspots.")


if __name__ == "__main__":
    main()
