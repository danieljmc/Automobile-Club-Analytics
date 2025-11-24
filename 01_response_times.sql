-- 01_response_times.sql
-- Calculates dispatch lag, travel time, on-scene time, and total handle time.
-- Creates a view roadside_response_times for reuse in BI tools.

USE aaa_roadside;

DROP VIEW IF EXISTS roadside_response_times;

CREATE VIEW roadside_response_times AS
SELECT
    r.request_id,
    r.member_id,
    r.request_ts,
    r.dispatch_ts,
    r.arrival_ts,
    r.completion_ts,
    TIMESTAMPDIFF(MINUTE, r.request_ts, r.dispatch_ts)   AS dispatch_lag_min,
    TIMESTAMPDIFF(MINUTE, r.dispatch_ts, r.arrival_ts)   AS travel_time_min,
    TIMESTAMPDIFF(MINUTE, r.arrival_ts, r.completion_ts) AS on_scene_time_min,
    TIMESTAMPDIFF(MINUTE, r.request_ts, r.completion_ts) AS total_handle_time_min,
    r.city,
    r.state,
    r.zone_id,
    r.road_type,
    r.issue_type,
    r.weather_severity
FROM roadside_requests r;

-- Example usage:
-- Average total handle time by city and road type
-- SELECT city, road_type, AVG(total_handle_time_min) AS avg_total_handle_time
-- FROM roadside_response_times
-- GROUP BY city, road_type
-- ORDER BY avg_total_handle_time DESC;
