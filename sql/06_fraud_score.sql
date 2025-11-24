-- 06_fraud_score.sql
-- Combines multiple signals into a simple fraud / abuse risk score.
-- Signals:
--  - Rolling 30-day call volume (high frequency)
--  - Shared VIN usage
--  - Far-from-home calls

USE aaa_roadside;

WITH rolling_30d AS (
    SELECT
        request_id,
        member_id,
        request_ts,
        COUNT(*) OVER (
            PARTITION BY member_id
            ORDER BY request_ts
            RANGE BETWEEN INTERVAL 30 DAY PRECEDING AND CURRENT ROW
        ) AS calls_last_30d
    FROM roadside_requests
),
call_activity AS (
    SELECT
        member_id,
        COUNT(*)            AS total_calls,
        MAX(calls_last_30d) AS max_calls_in_30d
    FROM rolling_30d
    GROUP BY member_id
),
shared_vins AS (
    SELECT
        vin
    FROM roadside_requests
    WHERE vin IS NOT NULL AND vin <> ''
    GROUP BY vin
    HAVING COUNT(DISTINCT member_id) > 1
),
member_vin_flags AS (
    SELECT
        r.member_id,
        CASE
            WHEN COUNT(DISTINCT r.vin) = 0 THEN 0
            ELSE 1
        END AS has_shared_vin
    FROM roadside_requests r
    JOIN shared_vins s
        ON r.vin = s.vin
    GROUP BY r.member_id
),
far_from_home AS (
    SELECT
        member_id,
        AVG(CASE WHEN zip_code = member_home_zip THEN 0 ELSE 1 END) AS pct_far_from_home
    FROM roadside_requests
    GROUP BY member_id
)
SELECT
    ca.member_id,
    ca.total_calls,
    ca.max_calls_in_30d,
    COALESCE(mvf.has_shared_vin, 0)      AS has_shared_vin,
    COALESCE(ffh.pct_far_from_home, 0.0) AS pct_far_from_home,
    -- Simple point-based fraud score (tune as desired)
    (
        CASE
            WHEN ca.max_calls_in_30d >= 4 THEN 40
            WHEN ca.max_calls_in_30d = 3 THEN 25
            WHEN ca.max_calls_in_30d = 2 THEN 10
            ELSE 0
        END
        +
        CASE
            WHEN COALESCE(mvf.has_shared_vin, 0) = 1 THEN 35 ELSE 0 END
        +
        CASE
            WHEN COALESCE(ffh.pct_far_from_home, 0.0) >= 0.75 THEN 25
            WHEN COALESCE(ffh.pct_far_from_home, 0.0) >= 0.50 THEN 15
            WHEN COALESCE(ffh.pct_far_from_home, 0.0) >= 0.25 THEN 5
            ELSE 0
        END
    ) AS fraud_score
FROM call_activity ca
LEFT JOIN member_vin_flags mvf
    ON ca.member_id = mvf.member_id
LEFT JOIN far_from_home ffh
    ON ca.member_id = ffh.member_id
ORDER BY fraud_score DESC, ca.member_id;

-- Optional materialization:
-- DROP TABLE IF EXISTS roadside_member_fraud_scores;
-- CREATE TABLE roadside_member_fraud_scores AS
-- SELECT * FROM (
--   [the SELECT above]
-- ) AS x;
