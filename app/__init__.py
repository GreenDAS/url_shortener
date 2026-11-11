# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/__init__.py
# Version: V1.1
# Description: Creates the Flask app object and loads its config from .env.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import Flask

from app.config import load_config

# ----------------------------------------------------------------------------
# App Setup
# ----------------------------------------------------------------------------
app = Flask(__name__)
app.config.update(load_config())  # MySQL Settings + Secret Key

from app import routes  # noqa: E402  Imported Last So Routes Can Use "app"
