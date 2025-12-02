# AAA Roadside Analytics Project

This repository is a **full end-to-end analytics and optimization project** built around synthetic roadside assistance data. It demonstrates:

- SQL data modeling and analytical querying  
- Python-based forecasting, clustering, and optimization  
- Power BI dashboards for operational insight  
- A repeatable ETL + modeling pipeline using MySQL + Python  

The scenario represents an auto club (e.g., AAA) analyzing:

- Call volume patterns  
- Response time performance  
- Member behavior and fraud indicators  
- Spatial hotspots  
- Forecasted demand  
- Optimal truck staffing by hour and zone  

This project is built entirely on a **synthetic dataset**, generated programmatically.

---

## 📁 Repository Structure

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
│   ├── Synthetic_Roadside.py
│   ├── 02a_assign_zones.py
│   ├── 01_demand_forecast_time.py
│   ├── 02_spatial_hotspots.py
│   └── 03_truck_staffing_optimization.py
│
└── powerbi/
    ├── roadside_dashboard.pbix         # (placeholder)
    ├── heatmap_visuals.png             # optional exports
    ├── fraud_score_visuals.png
    └── forecast_staffing_visuals.png
```

---

# 🚦 1. Data Layer (Synthetic → SQL)

### `python/Synthetic_Roadside.py`

Generates the synthetic roadside dataset with:

- timestamps for request → dispatch → arrival → completion  
- geo-coordinates (lat/lng)  
- city, state, ZIP  
- vehicle & member attributes  
- issue types  
- membership metadata  

The script writes the CSV twice:

1. To the project directory  
2. To MySQL’s `secure_file_priv` directory so `LOAD DATA INFILE` can import it  

---

### `sql/00_schema_and_seed_data.sql`

This script:

1. Creates the `aaa_roadside` database  
2. Creates the master fact table: `roadside_requests`  
3. Includes a nullable `zone_id` column (populated later by clustering)  
4. Contains an optional `LOAD DATA INFILE` block to ingest the synthetic CSV  

Run this before any other SQL or Python step:

```sql
SOURCE sql/00_schema_and_seed_data.sql;
```

---

# 🔍 2. SQL Analytical Layer

These scripts build reusable views for BI and fraud analysis.

### `01_response_times.sql`

Creates **`roadside_response_times`**, a view computing:

- dispatch lag  
- travel time  
- on-scene time  
- total handle time  

Used for operational performance dashboards.

---

### `02_heatmap_dow_hour.sql`

Creates **`roadside_calls_dow_hour`**, a day-of-week × hour-of-day matrix for call volume.  
Perfect for heatmaps in Power BI.

---

### `03_rolling_30_day_calls.sql`

Uses window functions to compute each member’s:

- rolling 30-day call count  
- max calls in any 30-day period  
- total calls  

This identifies unusual caller frequency.

---

### `04_vin_sharing.sql`

Flags possible **VIN-sharing fraud**:

- Identifies VINs linked to multiple member IDs  
- Flags affected members  

---

### `05_far_from_home.sql`

Creates **`roadside_far_from_home`**, which flags calls **outside** the member’s home ZIP.  
Useful for fraud scoring and behavioral profiling.

---

### `06_fraud_score.sql`

Combines:

- max 30-day call volume  
- shared VIN flag  
- % of calls far from home  

Into a simple **0–100 fraud score** with transparent weighting.

---

# 🧠 3. Python Modeling Layer

This is where clustering, forecasting, and optimization occur.

## Step 1 — Assign Zones from GPS  
### `python/02a_assign_zones.py`

Because the synthetic data has no operational zones, DBSCAN is used to identify spatial clusters.  
This script:

- Loads all lat/lng points  
- Runs DBSCAN with a haversine distance metric  
- Maps clusters → zone IDs (`1, 2, 3…`)  
- Noise points → `zone_id = 0`  
- **Writes zone_id back into `roadside_requests`**  

This must be run **before any forecasting or staffing**.

---

## Step 2 — Hourly Demand Forecasting  
### `python/01_demand_forecast_time.py`

For each zone:

1. Aggregates call volume per hour  
2. Ensures continuous hourly ranges  
3. Fits Holt–Winters (weekly seasonality) when possible  
4. Falls back to naive mean when short history  
5. Writes forecasts to:

   **`roadside_demand_forecast_hourly`**

Columns include:

- `ts`
- `zone_id`
- `forecast_calls`
- confidence bands (`lower_80`, `upper_80`)
- model used

These forecasts feed into Power BI and staffing optimization.

---

## Step 3 — Spatial Hotspot Detection  
### `python/02_spatial_hotspots.py`

Finds persistent spatial density clusters:

- Uses DBSCAN on lat/lng  
- Computes cluster centroids  
- Calculates a `hotspot_score` (cluster size)  
- Writes to:

  **`roadside_hotspots`**

Used for map visuals and possible future dynamic routing.

---

## Step 4 — Truck Staffing Optimization  
### `python/03_truck_staffing_optimization.py`

Using the demand forecast:

- For each hour and zone  
- Builds an integer linear program (PuLP)  
- Decision: number of trucks per zone  
- Objective: minimize total trucks  
- Constraint: trucks × capacity ≥ forecasted demand × target service level  

Example:  
> “At least 90% of expected calls must be coverable by assigned trucks.”

Writes results to:

**`roadside_staffing_plan`**

This provides a full **hour-by-hour, zone-by-zone staffing plan**.

---

# 📊 4. Power BI Dashboard

Connect Power BI Desktop to MySQL (`aaa_roadside`) and import:

- `roadside_requests`  
- `roadside_response_times`  
- `roadside_calls_dow_hour`  
- `roadside_far_from_home`  
- `roadside_demand_forecast_hourly`  
- `roadside_hotspots`  
- `roadside_staffing_plan`  
- (optional) materialized fraud scores  

### Recommended Report Tabs

#### **1. Operations Overview**
- Response time KPIs  
- Trends by city/zone  
- Issue type distribution  

#### **2. Volume Heatmap**
- Day-of-week × hour-of-day matrix  
- Peak volume identification  

#### **3. Fraud & Risk**
- Member fraud score table  
- Top suspicious members  
- VIN-sharing details  

#### **4. Forecast & Staffing**
- Hourly forecast line charts  
- Hotspot map  
- Truck staffing recommendations  

---

# 🔁 Pipeline Order (End-to-End)

This is the correct full-run order:

### **1. Generate synthetic data**
```bash
python python/Synthetic_Roadside.py
```

### **2. Run schema + import**
```sql
SOURCE sql/00_schema_and_seed_data.sql;
```

### **3. Populate zones**
```bash
python python/02a_assign_zones.py
```

### **4. Create views (SQL 01–06)**
Run each SQL file or source them together.

### **5. Generate forecasts**
```bash
python python/01_demand_forecast_time.py
```

### **6. Produce hotspot summaries**
```bash
python python/02_spatial_hotspots.py
```

### **7. Recommend staffing**
```bash
python python/03_truck_staffing_optimization.py
```

### **8. Visualize in Power BI**

---

# ✔ Summary

This project demonstrates:

- Advanced SQL analytics (window functions, fraud logic, KPI views)
- Spatial clustering (DBSCAN with haversine distance)
- Time series forecasting (Holt–Winters)
- Linear optimization (PuLP)
- A clean ETL → modeling → BI pipeline
- A realistic operational analytics scenario (AAA-style roadside support)
