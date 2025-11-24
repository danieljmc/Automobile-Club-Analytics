-- 02_heatmap_dow_hour.sql
-- Aggregates call volume by day-of-week and hour-of-day for heatmap visuals.

USE aaa_roadside;

DROP VIEW IF EXISTS roadside_calls_dow_hour;

CREATE VIEW roadside_calls_dow_hour AS
SELECT
    DAYOFWEEK(request_ts) AS day_of_week,   -- 1=Sunday, 7=Saturday
    HOUR(request_ts)      AS hour_of_day,
    COUNT(*)              AS call_count
FROM roadside_requests
GROUP BY DAYOFWEEK(request_ts), HOUR(request_ts);

-- Example usage:
-- SELECT * FROM roadside_calls_dow_hour ORDER BY day_of_week, hour_of_day;
