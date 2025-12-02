import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import string

# -----------------------------
# CONFIGURATION
# -----------------------------
N_RECORDS = 5000

# If you already have data in MySQL and your last request_id is, say, 10,000,
# set this to 10001 so there are no PK collisions.
START_REQUEST_ID = 1

# Date range for synthetic requests
START_DATE = datetime(2024, 1, 1)
END_DATE   = datetime(2024, 3, 31, 23, 59, 59)

np.random.seed(42)
random.seed(42)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def random_timestamp(start: datetime, end: datetime) -> datetime:
    """Generate a random datetime between start and end."""
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)

def generate_vin():
    """Generate a fake VIN-like string (not real, just looks plausible)."""
    chars = string.ascii_uppercase + string.digits
    # Exclude I, O, Q commonly omitted in real VINs, but this is synthetic anyway.
    chars = chars.replace("I", "").replace("O", "").replace("Q", "")
    return "".join(random.choices(chars, k=17))

def random_choice_with_weights(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

# -----------------------------
# SETUP: REGIONS / HOTSPOTS
# -----------------------------
# A few "zones" (you can customize these)
ZONES = [
    {
        "city": "Fall River",
        "state": "MA",
        "zip_codes": ["02720", "02721", "02723", "02724"],
        "center_lat": 41.700,
        "center_lon": -71.155
    },
    {
        "city": "Providence",
        "state": "RI",
        "zip_codes": ["02903", "02904", "02905", "02908"],
        "center_lat": 41.823,
        "center_lon": -71.412
    },
    {
        "city": "Warwick",
        "state": "RI",
        "zip_codes": ["02886", "02888", "02889"],
        "center_lat": 41.700,
        "center_lon": -71.416
    }
]

# Flat list of all ZIPs for "far from home" logic
ALL_ZIPS = (
    ZONES[0]["zip_codes"]
    + ZONES[1]["zip_codes"]
    + ZONES[2]["zip_codes"]
)

ROAD_TYPES = ["HIGHWAY", "URBAN", "RURAL"]
ROAD_TYPE_WEIGHTS = [0.6, 0.3, 0.1]

ISSUE_TYPES = ["TOW", "JUMP", "LOCKOUT", "TIRE", "OUT_OF_FUEL"]
ISSUE_TYPE_WEIGHTS = [0.4, 0.2, 0.15, 0.2, 0.05]

CALL_SOURCES = ["PHONE", "APP", "WEB", "PARTNER"]
CALL_SOURCE_WEIGHTS = [0.6, 0.25, 0.1, 0.05]

# We'll assume 50 trucks
TRUCK_IDS = list(range(100, 150))

# -----------------------------
# CREATE BASE RECORDS
# -----------------------------

records = []

for i in range(N_RECORDS):
    request_id = START_REQUEST_ID + i

    # Pick a zone
    zone = random.choice(ZONES)
    city = zone["city"]
    state = zone["state"]
    zip_code = random.choice(zone["zip_codes"])

    # Lat/long around the center with a small random offset
    latitude = zone["center_lat"] + np.random.normal(scale=0.02)
    longitude = zone["center_lon"] + np.random.normal(scale=0.02)

    # Time with some realistic patterns:
    # - More calls during rush hours (7–9am, 4–7pm)
    # - More calls on weekends
    # Generate a random timestamp, then "bias" it a bit
    base_ts = random_timestamp(START_DATE, END_DATE)
    hour = base_ts.hour
    dow = base_ts.weekday()  # 0=Mon, 6=Sun

    # Slight bias: if off-peak, sometimes resample into peak
    if hour not in [7, 8, 9, 16, 17, 18, 19] and random.random() < 0.3:
        # Force into a peak-ish hour
        peak_hours = [7, 8, 9, 16, 17, 18, 19]
        new_hour = random.choice(peak_hours)
        base_ts = base_ts.replace(
            hour=new_hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )

    # Slight extra weekend bias
    if dow >= 5 and random.random() < 0.3:
        # Nudge timestamp slightly to simulate clusters
        base_ts += timedelta(minutes=random.randint(-30, 30))

    request_ts = base_ts

    # Timestamps: dispatch after request, arrival after dispatch, completion after arrival
    dispatch_delay_min = random.randint(1, 20)
    arrival_delay_min = random.randint(5, 45)
    completion_delay_min = random.randint(10, 90)

    dispatch_ts = request_ts + timedelta(minutes=dispatch_delay_min)
    arrival_ts = dispatch_ts + timedelta(minutes=arrival_delay_min)
    completion_ts = arrival_ts + timedelta(minutes=completion_delay_min)

    # Truck, member, VIN, etc.
    truck_id = random.choice(TRUCK_IDS)

    member_id = random.randint(1000, 9999)

    # membership start up to 10 years before the request
    max_years_back = 10 * 365
    membership_offset_days = random.randint(0, max_years_back)
    membership_start = request_ts - timedelta(days=membership_offset_days)

    # 70% of the time, member lives in the same ZIP where service occurs
    if random.random() < 0.7:
        member_home_zip = zip_code
    else:
        # 30% of the time, member lives in a different ZIP
        other_zips = [z for z in ALL_ZIPS if z != zip_code]
        member_home_zip = random.choice(other_zips)

    road_type = random_choice_with_weights(ROAD_TYPES, ROAD_TYPE_WEIGHTS)
    issue_type = random_choice_with_weights(ISSUE_TYPES, ISSUE_TYPE_WEIGHTS)
    call_source = random_choice_with_weights(CALL_SOURCES, CALL_SOURCE_WEIGHTS)

    # miles_towed: depends loosely on road_type and issue_type
    if issue_type == "TOW":
        if road_type == "HIGHWAY":
            miles_towed = max(0.5, np.random.normal(loc=15, scale=8))
        else:
            miles_towed = max(0.5, np.random.normal(loc=8, scale=5))
    else:
        # non-tow services often 0 miles
        if random.random() < 0.7:
            miles_towed = 0.0
        else:
            miles_towed = max(0.5, np.random.normal(loc=5, scale=3))

    miles_towed = round(float(miles_towed), 1)

    vin = generate_vin()

    records.append(
        dict(
            request_id=request_id,
            member_id=member_id,
            request_ts=request_ts,
            dispatch_ts=dispatch_ts,
            arrival_ts=arrival_ts,
            completion_ts=completion_ts,
            latitude=round(latitude, 6),
            longitude=round(longitude, 6),
            zip_code=zip_code,
            city=city,
            state=state,
            road_type=road_type,
            issue_type=issue_type,
            truck_id=truck_id,
            vin=vin,
            miles_towed=miles_towed,
            call_source=call_source,
            membership_start=membership_start,
            member_home_zip=member_home_zip,
        )
    )

df = pd.DataFrame(records)

# -----------------------------
# INJECT SOME FRAUD / ANOMALIES
# -----------------------------

# 1) Duplicate VINs used many times (potential fraud)
num_fraud_vins = 20
fraud_vins = [generate_vin() for _ in range(num_fraud_vins)]

# Randomly pick ~5–15 rows per fraud VIN and assign that VIN
for fv in fraud_vins:
    idxs = df.sample(random.randint(5, 15)).index
    df.loc[idxs, "vin"] = fv

# 2) Overlapping jobs for the same truck (truck seems to be in two places at once)
# Pick some trucks and force overlapping arrival/completion windows
overlap_trucks = random.sample(TRUCK_IDS, 5)
for t in overlap_trucks:
    truck_rows = df[df["truck_id"] == t].sample(5, replace=False)
    # Force them to all overlap within a 1-hour window
    base_time = random_timestamp(START_DATE, END_DATE)
    for j, idx in enumerate(truck_rows.index):
        request_ts = base_time + timedelta(minutes=j * 5)
        dispatch_ts = request_ts + timedelta(minutes=5)
        arrival_ts = dispatch_ts + timedelta(minutes=5)
        completion_ts = arrival_ts + timedelta(minutes=20)

        df.loc[idx, "request_ts"] = request_ts
        df.loc[idx, "dispatch_ts"] = dispatch_ts
        df.loc[idx, "arrival_ts"] = arrival_ts
        df.loc[idx, "completion_ts"] = completion_ts

# 3) Impossible miles_towed (too many miles in too little time)
# e.g., 200 miles towed in 15 minutes
fraud_miles_rows = df.sample(30).index
df.loc[fraud_miles_rows, "miles_towed"] = 200.0

# -----------------------------
# FINAL CLEANUP & EXPORT
# -----------------------------

# Sort by request_ts for readability
df = df.sort_values("request_ts").reset_index(drop=True)

# Format datetime columns as strings MySQL likes
datetime_cols = ["request_ts", "dispatch_ts", "arrival_ts", "completion_ts", "membership_start"]
for col in datetime_cols:
    df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

# Write to working directory
output_file = "synthetic_roadside_requests.csv"
df.to_csv(output_file, index=False)

# Write to MySQL secure upload directory
output_file_secure = r"C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/synthetic_roadside_requests.csv"
df.to_csv(output_file_secure, index=False)

