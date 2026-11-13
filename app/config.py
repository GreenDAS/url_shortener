# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/config.py
# Version: V1.2
# Description: Reads the app settings (MySQL connection, secret key) from the
#              .env file and environment variables (spec DB-2, DB-5).
#
#              Where a setting comes from, first match wins:
#                1. A real environment variable (e.g. set by Docker or the
#                   shell). load_dotenv(override=False) never replaces these.
#                2. The .env file in the working folder (copied from
#                   .env.example, never committed).
#                3. The default written in load_config() below.
#              app/__init__.py calls load_config() once at startup and puts
#              the result into app.config. app/db.py then reads the MYSQL_*
#              keys from app.config when it opens a connection. This file is
#              the ONLY place with MySQL defaults (URL-26), db.py has none.
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import os  # os.environ Holds The Environment Variables

from dotenv import load_dotenv  # python-dotenv: Copies .env Lines Into os.environ

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DEFAULT_MYSQL_HOST = "host.docker.internal"  # Host Machine As Seen From The Container
DEFAULT_MYSQL_PORT = 3307  # Port The MySQL Container Publishes On The Host
DEFAULT_MYSQL_DB = "url_shortener"  # Database (Schema) Name

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def load_config(env_file=None):
    """
    Builds the Flask config dict from the .env file and the environment.

    Steps:
      1. load_dotenv() reads the .env file (if there is one) and copies each
         NAME=value line into os.environ, skipping any name that is already
         set so real environment variables win.
      2. Each setting is then read from os.environ with a fallback default.
         MYSQL_PORT is turned into an int since everything in os.environ is
         a string.

    Arg1 = env_file, path to a .env file (None = search for ".env" from the working folder)
    Returns: dict with MYSQL_HOST, MYSQL_PORT (int), MYSQL_USER, MYSQL_PASSWORD,
             MYSQL_DB and SECRET_KEY, ready for app.config.update()
    Raises: ValueError if MYSQL_PORT is set to something that is not a number
    """
    load_dotenv(env_file, override=False)  # Real Environment Variables Win Over .env

    return {
        "MYSQL_HOST": os.environ.get("MYSQL_HOST", DEFAULT_MYSQL_HOST),  # Where MySQL Runs
        "MYSQL_PORT": int(os.environ.get("MYSQL_PORT", DEFAULT_MYSQL_PORT)),  # String -> int
        "MYSQL_USER": os.environ.get("MYSQL_USER", ""),  # App's MySQL Account (DB-3)
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
        "MYSQL_DB": os.environ.get("MYSQL_DB", DEFAULT_MYSQL_DB),  # Database (Schema) Name
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-only-not-secret"),  # Signs The Session Cookie
    }
