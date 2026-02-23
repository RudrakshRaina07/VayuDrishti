CREATE DATABASE vayudrishti;
USE vayudrishti;

CREATE TABLE pending_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120),
    dob VARCHAR(20),
    phone VARCHAR(20),
    email VARCHAR(120),
    department VARCHAR(120),
    designation VARCHAR(120)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120),
    email VARCHAR(120),
    username VARCHAR(80),
    password_hash VARCHAR(255),
    role VARCHAR(20)
);

USE vayudrishti;
CREATE TABLE traffic_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    junction VARCHAR(10),
    density INT,
    aqi INT,
    green_time INT,
    pollution_cost FLOAT,
    event_time INT,          -- epoch seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO traffic_events
(junction, density, aqi, green_time, pollution_cost, event_time)
VALUES
('A', 78, 102, 42, 81.3, 1707400000);

SELECT
    junction,
    window_start,
    AVG(density) AS avg_density,
    MAX(density) AS max_density,
    AVG(aqi) AS avg_aqi,
    CASE
        WHEN AVG(density) > 70 THEN 'CONGESTED'
        ELSE 'NORMAL'
    END AS congestion_status
FROM (
    SELECT
        junction,
        density,
        aqi,
        FLOOR(event_time / 300) * 300 AS window_start
    FROM traffic_events
) t
GROUP BY
    junction,
    window_start
ORDER BY
    window_start DESC;

CREATE INDEX idx_event_time ON traffic_events(event_time);
CREATE INDEX idx_junction_time ON traffic_events(junction, event_time);


DELETE FROM users
WHERE name = 'Rudraksh Raina';

SELECT * FROM users;

SELECT * FROM pending_users;

USE vayudrishti;
CREATE TABLE history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aqi INT,
    traffic INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO history (aqi, traffic)
SELECT
  FLOOR(60 + RAND() * 80),
  FLOOR(20 + RAND() * 70)
FROM information_schema.tables
LIMIT 50;

ALTER TABLE history
ADD COLUMN junction VARCHAR(10);

DESCRIBE history;

SELECT COUNT(*) FROM history;

USE vayudrishti;
UPDATE users
SET role = 'officelogin'

WHERE username = 'rudraksh007';

SET SQL_SAFE_UPDATES = 0;
SET SQL_SAFE_UPDATES = 1;

CREATE TABLE traffic_control_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50),
    junction VARCHAR(10),
    aqi INT,
    density INT,
    green_time INT,
    mode ENUM('NORMAL','OPTIMIZED','EMERGENCY'),
    overridden BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE history ADD COLUMN city VARCHAR(50);



DESCRIBE history;
SELECT city, COUNT(*) FROM history GROUP BY city;

ALTER TABLE users
ADD COLUMN department VARCHAR(120),
ADD COLUMN designation VARCHAR(120);
UPDATE users
SET
  department = 'Air Quality',
  designation = 'Field Officer'
WHERE email = '1819rudraksh@gmail.com';

SELECT COUNT(*) 
FROM history 
WHERE city = 'Mumbai';
SELECT DISTINCT city FROM history;

DELETE FROM history WHERE city IS NULL;

