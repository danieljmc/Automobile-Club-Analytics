import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from math import radians, cos, sin, asin, sqrt

# ---------------------------------------------------
# Load your synthetic roadside data
# ---------------------------------------------------
df = pd.read_csv("synthetic_roadside_requests.csv")

coords = df[["latitude", "longitude"]].values


# ---------------------------------------------------
# Haversine distance (in KM) for DBSCAN
# ---------------------------------------------------
def haversine_km(p1, p2):
    lat1, lon1 = p1
    lat2, lon2 = p2

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius in KM
    return c * r


# sklearn expects a *callable metric* that takes 2 rows, so wrap it
def metric(a, b):
    return haversine_km(a, b)


# ---------------------------------------------------
# Parameter sweep
# ---------------------------------------------------
eps_values = [0.5, 1.0, 1.5, 2.0]
min_samples = 5

print("\n=== DBSCAN EPS Parameter Sweep ===\n")

for eps in eps_values:
    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric=metric
    ).fit(coords)

    labels = clustering.labels_
    unique_clusters = set(labels)

    # Noise points have label = -1
    num_noise = list(labels).count(-1)

    # Number of REAL clusters (exclude -1)
    num_clusters = len([c for c in unique_clusters if c != -1])

    print(f"EPS = {eps} km:")
    print(f"  → Real clusters found: {num_clusters}")
    print(f"  → Noise points: {num_noise}")

    # Optional: show cluster sizes (excluding -1)
    cluster_sizes = (
        pd.Series(labels)
        .value_counts()
        .sort_index()
        .rename("count")
    )

    print("  → Cluster sizes:")
    print(cluster_sizes.to_string())
    print("\n")
