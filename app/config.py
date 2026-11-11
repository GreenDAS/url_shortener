# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/config.py
# Version: V1.0
# Description: Reads the app settings (MySQL connection, secret key) from the
#              .env file and environment variables (spec DB-2, DB-5).
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import os

from dotenv import load_dotenv

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DEFAULT_MYSQL_HOST = "host.docker.internal"  # Host Machine As Seen From The Container
DEFAULT_MYSQL_PORT = 3307  # Port The MySQL Container Publishes On The Host

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def load_config(env_file=None):
    """
    Builds the Flask config dict from the .env file and the environment.
    Arg1 = env_file, path to a .env file (None = search for ".env" from the working folder)
    Returns: dict of config values ready for app.config.update()
    """
    load_dotenv(env_file, override=False)  # Real Environment Variables Win Over .env

    return {
        "MYSQL_HOST": os.environ.get("MYSQL_HOST", DEFAULT_MYSQL_HOST),
        "MYSQL_PORT": int(os.environ.get("MYSQL_PORT", DEFAULT_MYSQL_PORT)),
        "MYSQL_USER": os.environ.get("MYSQL_USER", ""),
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
        "MYSQL_DB": os.environ.get("MYSQL_DB", "url_shortener"),
        "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-only-not-secret"),
    }
