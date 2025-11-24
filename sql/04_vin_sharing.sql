-- 04_vin_sharing.sql
-- Identifies VINs that are shared across multiple members and flags members.

USE aaa_roadside;

-- VINs that appear with more than one distinct member_id
WITH shared_vins AS (
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
)
SELECT *
FROM member_vin_flags
ORDER BY has_shared_vin DESC, member_id;

-- Optional persistent table:
-- DROP TABLE IF EXISTS roadside_member_vin_flags;
-- CREATE TABLE roadside_member_vin_flags AS
-- SELECT * FROM member_vin_flags;
