-- ----------------------------------------------------------------------------
-- Author: Daniel S.
-- Date: 11/10/2026
-- File: app/schema.sql
-- Version: V1.1
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

-- ----------------------------------------------------------------------------
-- URLs Table (URL-10)
-- ----------------------------------------------------------------------------
-- One row per short link. "code" is the part after the domain
-- (url.short.com/<code>). Deleting a user deletes their links too.
CREATE TABLE IF NOT EXISTS urls (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT           NOT NULL,                         -- Owner, Points At users.id
    code       VARCHAR(32)   COLLATE utf8mb4_bin NOT NULL UNIQUE, -- Short Code, Case Sensitive (aB12 != AB12)
    long_url   VARCHAR(2048) NOT NULL,                         -- Where The Redirect Goes
    clicks     INT           NOT NULL DEFAULT 0,               -- Times The Short Link Was Used
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
