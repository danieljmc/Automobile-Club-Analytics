-- 05_far_from_home.sql
-- Flags whether a request is far from the member's home ZIP based on ZIP mismatch.

USE aaa_roadside;

DROP VIEW IF EXISTS roadside_far_from_home;

CREATE VIEW roadside_far_from_home AS
SELECT
    request_id,
    member_id,
    request_ts,
    zip_code          AS service_zip,
    member_home_zip,
    CASE
        WHEN zip_code = member_home_zip THEN 0
        ELSE 1
    END AS is_far_from_home,
    miles_towed,
    city,
    state
FROM roadside_requests;

-- Example usage:
-- SELECT state, AVG(is_far_from_home) AS pct_far
-- FROM roadside_far_from_home
-- GROUP BY state;
