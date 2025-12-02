
# Automobile Club Analytics

This project simulates a complete roadside assistance analytics workflow using synthetic data. It demonstrates how SQL, Python, and Power BI can work together to support operational decisions such as staffing, fraud detection, and performance monitoring. The dataset is entirely synthetic and modeled after real-world AAA‑style roadside operations.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Power BI](https://img.shields.io/badge/PowerBI-Dashboard-yellow)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)

---

# 🚀 Quick Start

```bash
git clone https://github.com/danieljmc/Automobile-Club-Analytics.git
cd Automobile-Club-Analytics
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Generate synthetic data:

```bash
python python/Synthetic_Roadside.py
```

Load schema + data into MySQL:

```sql
SOURCE sql/00_schema_and_seed_data.sql;
```

Run modeling steps:

```bash
python python/02a_assign_zones.py
python python/01_demand_forecast_time.py
python python/02_spatial_hotspots.py
python python/03_truck_staffing_optimization.py
```

Open Power BI and connect to the `aaa_roadside` MySQL database.

---

# 🧰 Tech Stack

- **Database:** MySQL  
- **Python:** pandas, statsmodels, scikit‑learn (DBSCAN), PuLP  
- **Visualization:** Power BI  
- **Methods:** Holt‑Winters forecasting, clustering, optimization, SQL window functions  

---

# 📊 Business Impact Overview

This project demonstrates how an auto club could:

- Forecast hourly demand by zone  
- Staff trucks efficiently while meeting SLA targets  
- Detect suspicious activity such as VIN sharing or abnormal call patterns  
- Identify geographic hotspots to reduce travel times  
- Build a repeatable analytics workflow across SQL, Python, and Power BI  

---

# 📂 Repository Structure

```text
sql/
  00_schema_and_seed_data.sql
  01_response_times.sql
  02_heatmap_dow_hour.sql
  03_rolling_30_day_calls.sql
  04_vin_sharing.sql
  05_far_from_home.sql
  06_fraud_score.sql

python/
  Synthetic_Roadside.py
  02a_assign_zones.py
  01_demand_forecast_time.py
  02_spatial_hotspots.py
  03_truck_staffing_optimization.py

powerbi/
  roadside_dashboard.pbix
  Exec_Summary.png
  Forcasting.png
  Fraud_Indicators.png
```

---

# 🧩 1. Data Layer — Synthetic Data → SQL

## `Synthetic_Roadside.py`
Creates a realistic synthetic dataset containing timestamps, member data, VINs, locations, and issue types. Generates a CSV that MySQL imports via `LOAD DATA INFILE`.

## `00_schema_and_seed_data.sql`
Creates the `aaa_roadside` database and the main fact table `roadside_requests`. Also loads the generated CSV.

---

# 🧮 2. SQL Analytical Layer

### `01_response_times.sql`
Generates the `roadside_response_times` view containing dispatch lag, travel time, on‑scene duration, and total handle time.

### `02_heatmap_dow_hour.sql`
Creates a day‑of‑week × hour heatmap table for Power BI visuals.

### `03_rolling_30_day_calls.sql`
Uses window functions to compute rolling 30‑day call counts and identify heavy users.

### `04_vin_sharing.sql`
Flags VINs associated with multiple member IDs.

### `05_far_from_home.sql`
Determines when calls occur outside a member’s home ZIP.

### `06_fraud_score.sql`
Combines multiple signals into a 0–100 fraud score.

---

# 🧠 3. Python Modeling Layer

### `02a_assign_zones.py`
Runs DBSCAN clustering on lat/lng coordinates to assign operational zone IDs and stores them in MySQL.

### `01_demand_forecast_time.py`
Creates hourly forecasts for each zone using Holt‑Winters. Writes results to `roadside_demand_forecast_hourly`.

### `02_spatial_hotspots.py`
Detects dense geographic clusters and writes them to `roadside_hotspots`.

### `03_truck_staffing_optimization.py`
Optimizes hourly truck staffing using linear programming. Writes results to `roadside_staffing_plan`.

---

# 📊 4. Power BI Dashboard

Below are sample visuals embedded from the repository:

### **Executive Summary**
![Executive Summary](https://github.com/danieljmc/Automobile-Club-Analytics/blob/main/PowerBI/Exec_Summary.png?raw=true)

### **Forecasting & Staffing**
![Forecasting](https://github.com/danieljmc/Automobile-Club-Analytics/blob/main/PowerBI/Forcasting.png?raw=true)

### **Fraud Indicators**
![Fraud Indicators](https://github.com/danieljmc/Automobile-Club-Analytics/blob/main/PowerBI/Fraud_Indicators.png?raw=true)

---

# 🔁 End‑to‑End Pipeline Order

1. Generate synthetic data  
2. Load schema + data into MySQL  
3. Assign spatial zones  
4. Create SQL analytical views  
5. Run forecasting  
6. Detect hotspots  
7. Run staffing optimization  
8. Build visuals in Power BI  

---

# ✅ Summary

This project reflects a real-world analytics workflow, combining:

- SQL engineering  
- Python modeling  
- Geospatial analysis  
- Forecasting  
- Optimization  
- Dashboarding  

It is designed as a job‑ready portfolio example demonstrating operational analytics for roadside assistance organizations.

