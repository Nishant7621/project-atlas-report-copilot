-- MySQL initialization script for Project Atlas
-- Sets up database, primary read-write user, and strictly limited read-only user

CREATE DATABASE IF NOT EXISTS atlas_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create read-only user for SQL tool
CREATE USER IF NOT EXISTS 'atlas_ro'@'%' IDENTIFIED BY 'atlas_ro_pass';
GRANT SELECT ON atlas_db.reports TO 'atlas_ro'@'%';
GRANT SELECT ON atlas_db.market_metrics TO 'atlas_ro'@'%';
-- Notice: atlas_ro explicitly has NO access to clients table or escalations!

FLUSH PRIVILEGES;
