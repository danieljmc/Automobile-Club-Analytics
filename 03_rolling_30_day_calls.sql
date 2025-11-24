-- 03_rolling_30_day_calls.sql
-- Calculates per-member rolling 30-day call counts and aggregates.

USE aaa_roadside;

-- You can run this CTE as a standalone query in MySQL 8+.
-- If you prefer a persistent object, uncomment the CREATE TABLE or VIEW section.

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
        COUNT(*)                 AS total_calls,
        MAX(calls_last_30d)      AS max_calls_in_30d
    FROM rolling_30d
    GROUP BY member_id
)
SELECT *
FROM call_activity
ORDER BY max_calls_in_30d DESC, total_calls DESC;

-- If you want this as a table or view:
--
-- DROP TABLE IF EXISTS roadside_call_activity_30d;
-- CREATE TABLE roadside_call_activity_30d AS
-- SELECT * FROM call_activity;
