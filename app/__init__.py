# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/__init__.py
# Version: V1.2
# Description: Creates the Flask app object, loads its config from .env and
#              hooks up the database and every route module.
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

from app import db  # noqa: E402
db.init_app(app)  # MySQL Connection + "flask init-db" Command

from app import routes  # noqa: E402  Imported Last So Routes Can Use "app"
from app import accounts  # noqa: E402  Switch User (URL-12)
from app import redirect  # noqa: E402  /<code> Short Links (URL-11), Kept Last
