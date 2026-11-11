-- ----------------------------------------------------------------------------
-- Author: Daniel S.
-- Date: 11/10/2026
-- File: app/schema.sql
-- Version: V1.0
-- Description: Creates the MySQL tables the app needs. Run it with:
--              flask --app url_shortener init-db
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- Users Table (URL-9)
-- ----------------------------------------------------------------------------
-- One row per account. Passwords are never stored in plain text, only the
-- hash made by werkzeug's generate_password_hash().
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,                -- Login Name, No Duplicates
    password_hash VARCHAR(255) NOT NULL,                       -- Salted Hash, Not The Password
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
