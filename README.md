# Automobile Club Analytics

This project simulates a full roadside assistance analytics pipeline, including synthetic data generation, SQL analytics, forecasting, spatial clustering, fraud scoring, and Power BI dashboards.

## Quick Start

1. Clone the repo:
```bash
git clone https://github.com/danieljmc/Automobile-Club-Analytics.git
cd Automobile-Club-Analytics
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Generate synthetic data:
```bash
python python/Synthetic_Roadside.py
```

4. Load schema and seed data into MySQL:
```sql
SOURCE sql/00_schema_and_seed_data.sql;
```

5. Run analytics scripts:
```bash
python python/02a_assign_zones.py
python python/01_demand_forecast_time.py
python python/02_spatial_hotspots.py
python python/03_truck_staffing_optimization.py
```

6. Open Power BI:
Load `powerbi/roadside_dashboard.pbix` and connect to MySQL `aaa_roadside`.

## Tech Stack

- **Database:** MySQL  
- **Python:** pandas, statsmodels, scikit-learn (DBSCAN), PuLP  
- **Visualization:** Power BI  
- **Analytics Techniques:**  
  - Holt–Winters forecasting  
  - DBSCAN clustering  
  - Integer linear optimization  
  - SQL window functions for fraud scoring  

## Project Overview

```
Synthetic_Roadside.py --> roadside_requests (MySQL)
       |                    
       +--> SQL Views (response times, fraud, far-from-home, hourly aggregates)
       |
       +--> Python Models:
              - DBSCAN zones
              - Holt–Winters forecasts
              - Hotspot detection
              - Optimization for staffing
       |
       +--> Power BI Dashboards (Operations, Fraud, Staffing)
```

## Business Impact (Scenario)

This type of analytics solution helps an auto club:

- Identify peak demand patterns and staff accordingly.  
- Detect suspicious member behavior, shared VIN usage, and heavy call volume patterns.  
- Visualize spatial hotspots to position trucks more efficiently.  
- Quantify trade-offs between staffing levels, cost, and SLA performance.  

## Sample Dashboards

### Heatmap & Response Time  
![Heatmap](powerbi/heatmap_visuals.png)

### Fraud & Risk Overview  
![Fraud](powerbi/fraud_score_visuals.png)

## Repo Structure

```
sql/
  00_schema_and_seed_data.sql
  01_response_times.sql
  02_far_from_home.sql
  03_heatmap_bins.sql
  04_call_volume_by_hour.sql
  05_sql_setup_for_powerbi_dax.sql
  06_fraud_score.sql

python/
  Synthetic_Roadside.py
  01_demand_forecast_time.py
  02_spatial_hotspots.py
  02a_assign_zones.py
  03_truck_staffing_optimization.py

powerbi/
  roadside_dashboard.pbix
  *.png

```

## Future Enhancements

- Compare Holt–Winters with ARIMA and Prophet models.  
- Add supervised fraud detection using labeled training data.  
- Build a lightweight web UI for interacting with forecasts and staffing recommendations.  

---

*This repo is designed as a job‑ready analytics portfolio project demonstrating real-world SQL, Python, and BI workflows.*
