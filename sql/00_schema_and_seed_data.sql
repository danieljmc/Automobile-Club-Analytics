-- 00_schema_and_seed_data.sql
-- Creates the aaa_roadside database, roadside_requests table,
-- and inserts a small synthetic sample dataset.
-- Designed for MySQL 8+.

DROP DATABASE IF EXISTS aaa_roadside;
CREATE DATABASE aaa_roadside;
USE aaa_roadside;

DROP TABLE IF EXISTS roadside_requests;

CREATE TABLE roadside_requests (
    request_id        BIGINT PRIMARY KEY,
    member_id         BIGINT NOT NULL,
    request_ts        DATETIME NOT NULL,
    dispatch_ts       DATETIME NOT NULL,
    arrival_ts        DATETIME NOT NULL,
    completion_ts     DATETIME NOT NULL,
    latitude          DECIMAL(9,6),
    longitude         DECIMAL(9,6),
    zip_code          VARCHAR(10),
    city              VARCHAR(100),
    state             CHAR(2),
    road_type         VARCHAR(20),
    issue_type        VARCHAR(50),
    truck_id          INT,
    vin               VARCHAR(50),
    miles_towed       DECIMAL(6,1),
    call_source       VARCHAR(20),
    member_home_zip   VARCHAR(10),
    zone_id           INT,
    weather_severity  TINYINT,   -- 0=clear,1=rain,2=snow,3=storm
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Minimal seed data: feel free to regenerate with a Python script
-- or extend this manually. This is just enough to make the example
-- queries and Power BI visuals work.

INSERT INTO roadside_requests (
    request_id, member_id, request_ts, dispatch_ts, arrival_ts, completion_ts,
    latitude, longitude, zip_code, city, state, road_type, issue_type,
    truck_id, vin, miles_towed, call_source, member_home_zip, zone_id, weather_severity
) VALUES
    (1001, 501, '2025-01-01 08:05:00', '2025-01-01 08:07:00', '2025-01-01 08:20:00', '2025-01-01 08:50:00',
     41.700000, -71.100000, '02720', 'Fall River', 'MA', 'Highway', 'Flat tire',
     201, '1HGCM82633A004352', 5.0, 'Phone', '02720', 1, 0),
    (1002, 501, '2025-01-03 18:10:00', '2025-01-03 18:12:00', '2025-01-03 18:30:00', '2025-01-03 19:00:00',
     41.750000, -71.150000, '02904', 'Providence', 'RI', 'City', 'Dead battery',
     202, '1HGCM82633A004352', 0.0, 'App', '02720', 2, 1),
    (1003, 502, '2025-01-05 09:20:00', '2025-01-05 09:25:00', '2025-01-05 09:45:00', '2025-01-05 10:10:00',
     42.360000, -71.058900, '02108', 'Boston', 'MA', 'Highway', 'Engine issue',
     203, '1FTFW1EF1EKE12345', 12.0, 'Phone', '02110', 3, 2),
    (1004, 503, '2025-01-05 22:15:00', '2025-01-05 22:20:00', '2025-01-05 22:40:00', '2025-01-05 23:05:00',
     42.360500, -71.000000, '02110', 'Boston', 'MA', 'Highway', 'Tow request',
     203, '1FTFW1EF1EKE12345', 25.0, 'App', '02110', 3, 3),
    (1005, 504, '2025-01-06 14:05:00', '2025-01-06 14:08:00', '2025-01-06 14:25:00', '2025-01-06 14:55:00',
     41.490000, -71.310000, '02840', 'Newport', 'RI', 'City', 'Lockout',
     204, '2G1WF52E759123456', 0.0, 'Phone', '02840', 4, 0);
