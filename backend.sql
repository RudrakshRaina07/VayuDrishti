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

DELETE FROM users
WHERE name = 'Rudraksh Raina';

SELECT * FROM pending_users;
