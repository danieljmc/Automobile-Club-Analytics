# AAA Roadside Analytics Project

This repository is a **portfolio-ready analytics project** that walks through the full lifecycle:

1. **SQL analytics** on synthetic roadside assistance request data.  
2. **Power BI dashboards** built on top of SQL views and tables.  
3. **Python forecasting and optimization** for truck placement and staffing, writing results back to MySQL for visualization in Power BI.

The scenario is based on an auto club (e.g., AAA) that wants to:

- Understand response times and volume patterns.
- Detect possible abuse or fraud.
- Forecast future roadside demand.
- Recommend how many trucks to stage in each zone and hour.

---

## Repository Structure

```text
aaa-roadside-analytics/
│
├── README.md
│
├── sql/
│   ├── 00_schema_and_seed_data.sql
│   ├── 01_response_times.sql
│   ├── 02_heatmap_dow_hour.sql
│   ├── 03_rolling_30_day_calls.sql
│   ├── 04_vin_sharing.sql
│   ├── 05_far_from_home.sql
│   └── 06_fraud_score.sql
│
├── python/
│   ├── 01_demand_forecast_time.py
│   ├── 02_spatial_hotspots.py
│   └── 03_truck_staffing_optimization.py
│
└── powerbi/
    ├── roadside_dashboard.pbix        # (placeholder – built in Power BI Desktop)
    ├── heatmap_visuals.png            # (exported from Power BI)
    ├── fraud_score_visuals.png        # (exported from Power BI)
    └── forecast_staffing_visuals.png  # (exported from Power BI)
```

You can keep the Power BI folder as a placeholder initially and add the `.pbix` and PNG exports once your visuals are built.

---

## 1. SQL Layer

All SQL scripts target **MySQL 8+**.

### `sql/00_schema_and_seed_data.sql`

- Creates the database and main table:

  - `aaa_roadside`
  - `roadside_requests`

- To import the synthetic dataset, uncomment the LOAD DATA INFILE block in 00_schema_and_seed_data.sql and update the filepath to match your local MySQL secure_file_priv directory.
- Run this file **first**:

```sql
SOURCE sql/00_schema_and_seed_data.sql;
```

---

### `sql/01_response_times.sql`

Creates a view with detailed time metrics per request:

- `dispatch_lag_min` (request → dispatch)  
- `travel_time_min` (dispatch → arrival)  
- `on_scene_time_min` (arrival → completion)  
- `total_handle_time_min` (request → completion)

View created:

- `roadside_response_times`

Example usage:

```sql
SELECT city, road_type, AVG(total_handle_time_min) AS avg_total_handle_time
FROM roadside_response_times
GROUP BY city, road_type
ORDER BY avg_total_handle_time DESC;
```

---

### `sql/02_heatmap_dow_hour.sql`

Aggregates call volume by **day-of-week** and **hour-of-day** for heatmap visuals.

View created:

- `roadside_calls_dow_hour`

Columns:

- `day_of_week` (1 = Sunday … 7 = Saturday)  
- `hour_of_day` (0–23)  
- `call_count`

Use this as the **source for a matrix/heatmap visual** in Power BI.

---

### `sql/03_rolling_30_day_calls.sql`

Calculates **rolling 30‑day call activity per member** using window functions:

- For each member:
  - `total_calls`
  - `max_calls_in_30d` (max rolling 30‑day calls)

This script is written as a CTE + `SELECT` query. You can run it directly, or uncomment the `CREATE TABLE` section in the file to persist results as:

- `roadside_call_activity_30d`

---

### `sql/04_vin_sharing.sql`

Identifies **VINs shared across multiple member IDs**, which can be a fraud/abuse signal.

- Finds VINs linked to more than one distinct member.
- Flags members with a shared VIN:

  - `member_id`
  - `has_shared_vin` (0/1)

You can optionally persist the result as:

- `roadside_member_vin_flags`

(uncomment the `CREATE TABLE` statement in the script).

---

### `sql/05_far_from_home.sql`

Flags whether each request is **“far from home”** based on ZIP mismatch.

Creates view:

- `roadside_far_from_home`

Key columns:

- `service_zip`
- `member_home_zip`
- `is_far_from_home` (0/1)
- `miles_towed`, `city`, `state`, `zone_id`

This view feeds into the fraud score and can also be used for standalone analysis (e.g., % of calls far from home by state).

---

### `sql/06_fraud_score.sql`

Combines multiple signals into a **simple fraud / abuse score** per member:

Inputs:

- Rolling 30‑day call activity (`max_calls_in_30d`)
- Shared VIN flag (`has_shared_vin`)
- % of calls far from home (`pct_far_from_home`)

Output columns:

- `member_id`
- `total_calls`
- `max_calls_in_30d`
- `has_shared_vin`
- `pct_far_from_home`
- `fraud_score` (0–100, based on a simple point system)

You can turn this into a persistent table (e.g., `roadside_member_fraud_scores`) by uncommenting the `CREATE TABLE` block in the script.

---

## 2. Python Layer

Python scripts assume:

- You have a working MySQL instance with the `aaa_roadside` database.
- Your MySQL connection settings are provided via environment variables:

  - `AAA_DB_USER`
  - `AAA_DB_PWD`
  - `AAA_DB_HOST`
  - `AAA_DB_PORT` (optional – defaults to `3306`)

### Suggested Python Environment

```bash
pip install pandas sqlalchemy mysql-connector-python statsmodels scikit-learn pulp
```

---

### `python/01_demand_forecast_time.py`

**Goal:** Forecast hourly roadside call volume.

Workflow:

1. Connects to MySQL (`aaa_roadside`).
2. Aggregates call counts per hour (by `zone_id`).
3. Fits a time series model for each zone:
   - Holt‑Winters with weekly seasonality if enough history.
   - Falls back to a naive mean model otherwise.
4. Writes results to table:

   - `roadside_demand_forecast_hourly`

Columns:

- `ts` (hourly timestamp)
- `zone_id`
- `forecast_calls`
- `lower_80`
- `upper_80`
- `model_name`

This table is the input to Power BI’s **Forecast & Staffing** tab.

Run:

```bash
python python/01_demand_forecast_time.py
```

---

### `python/02_spatial_hotspots.py`

**Goal:** Identify spatial **hotspots** of roadside calls using clustering.

Workflow:

1. Pulls `latitude`, `longitude`, `zone_id`, and `request_ts` from `roadside_requests`.
2. Runs **DBSCAN** per zone using a haversine distance metric.
3. For each cluster (non‑noise), computes:

   - centroid latitude/longitude
   - `hotspot_score` = number of calls in the cluster

4. Writes results to:

   - `roadside_hotspots`

Columns:

- `as_of_date`
- `zone_id`
- `cluster_id`
- `centroid_lat`
- `centroid_lng`
- `hotspot_score`
- `method` (e.g., `"DBSCAN_haversine"`)

Run:

```bash
python python/02_spatial_hotspots.py
```

---

### `python/03_truck_staffing_optimization.py`

**Goal:** Recommend how many **trucks** to stage in each zone for each hour.

Workflow:

1. Reads forecasts from `roadside_demand_forecast_hourly`.
2. Uses a simple assumption for capacity:

   - Each truck can handle `CALLS_PER_TRUCK_PER_HOUR` calls.
   - Aim to cover `TARGET_SERVICE_LEVEL` (e.g., 90%) of forecasted demand.

3. Builds an integer programming model in **PuLP**:

   - Decision variable: number of trucks per zone per hour (must be integer).
   - Objective: minimize total number of trucks.
   - Constraint: truck capacity ≥ target demand.

4. Writes recommendations to:

   - `roadside_staffing_plan`

Columns:

- `ts`
- `zone_id`
- `recommended_trucks`
- `expected_calls`
- `target_service_lvl`
- `model_name`

Run:

```bash
python python/03_truck_staffing_optimization.py
```

---

## 3. Power BI Layer

In **Power BI Desktop**:

1. **Connect to MySQL**  
   - Data source: MySQL database  
   - Server: your MySQL host  
   - Database: `aaa_roadside`

2. **Import the key tables/views:**

   - `roadside_requests`
   - `roadside_response_times` (view)
   - `roadside_calls_dow_hour` (view)
   - `roadside_far_from_home` (view)
   - `roadside_member_fraud_scores` (if materialized)
   - `roadside_demand_forecast_hourly`
   - `roadside_hotspots`
   - `roadside_staffing_plan`

3. **Suggested Report Tabs:**

   - **Operations Overview**
     - KPIs: total calls, average response time, SLA %
     - Trend line: calls over time
     - Bar charts: response times by city/zone

   - **Volume Heatmap**
     - Matrix/heatmap using `roadside_calls_dow_hour`
     - Rows: day_of_week, Columns: hour_of_day, Values: call_count

   - **Fraud & Risk**
     - Table: member, total calls, max_calls_in_30d, fraud_score
     - Bar chart of fraud_score distribution
     - Drill-through to member-level detail

   - **Forecast & Staffing**
     - Line chart of forecasted calls (`roadside_demand_forecast_hourly`)
     - Map of hotspots (lat/long from `roadside_hotspots`)
     - Table or bar chart of recommended_trucks by zone/hour (`roadside_staffing_plan`)

4. Save your report as:

   - `powerbi/roadside_dashboard.pbix`

   and optionally export static PNGs of each tab into the same folder.

---

## How Everything Fits Together

- **SQL** defines the schema, cleans/aggregates operational data, and creates views for BI and fraud/risk analysis.
- **Python** adds:
  - Time series forecasting for call volume.
  - Spatial clustering to find hotspots.
  - Integer programming to recommend staffing levels.
- **Power BI** sits on top of both:
  - Visualizes current performance.
  - Surfaces fraud risk.
  - Shows future demand and recommended truck placement.



