-- ----------------------------------------------------------------------------
-- Author: Daniel S.
-- Date: 11/11/2026
-- File: app/schema.sql
-- Version: V1.3
-- Description: Creates the MySQL tables the app needs. Run it with:
--              flask --app url_shortener init-db
--
--              app/db.py's init_db() reads this file, strips the "--"
--              comments, splits it on ";" and runs each statement. Every
--              table uses IF NOT EXISTS so running it again is harmless.
--              Keep ";" and "--" out of string values, the simple splitter
--              in db.py does not understand quotes.
--              Spec sheet: docs/specs/database.md
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- Users Table (URL-9)
-- ----------------------------------------------------------------------------
-- One row per account. Passwords are never stored in plain text, only the
-- hash made by werkzeug's generate_password_hash().
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,              -- MySQL Picks The Next Number
    username      VARCHAR(50)  NOT NULL UNIQUE,                -- Login Name, No Duplicates
    password_hash VARCHAR(255) NOT NULL,                       -- Salted Hash, Not The Password
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP -- Filled In By MySQL On INSERT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; -- InnoDB Is Needed For FOREIGN KEY, utf8mb4 = Full Unicode

-- ----------------------------------------------------------------------------
-- URLs Table (URL-10)
-- ----------------------------------------------------------------------------
-- One row per short link. "code" is the part after the domain
-- (url.short.com/<code>). Deleting a user deletes their links too.
CREATE TABLE IF NOT EXISTS urls (
    id         INT AUTO_INCREMENT PRIMARY KEY,                 -- MySQL Picks The Next Number
    user_id    INT           NOT NULL,                         -- Owner, Points At users.id
    code       VARCHAR(32)   COLLATE utf8mb4_bin NOT NULL UNIQUE, -- Short Code, Case Sensitive (aB12 != AB12)
    long_url   VARCHAR(2048) NOT NULL,                         -- Where The Redirect Goes
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Newest First Sorting Uses This
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE -- Links Go Away With Their Owner
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; -- InnoDB Is Needed For FOREIGN KEY, utf8mb4 = Full Unicode
