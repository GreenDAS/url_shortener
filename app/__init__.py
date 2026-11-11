# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/__init__.py
# Version: V1.3
# Description: Creates the Flask app object, loads its config from .env and
#              hooks up the database and every route module.
#
#              This file runs once, the first time anything does
#              "from app import app" (url_shortener.py, Gunicorn, the tests).
#              The order of the steps below matters:
#                1. Make the Flask object.
#                2. Load the settings into app.config (app/config.py), so
#                   everything after this can read MYSQL_* and SECRET_KEY.
#                3. Hook the database in (app/db.py): closes the MySQL
#                   connection after each request, adds "flask init-db".
#                4. Import the route modules. Each one does
#                   "from app import app" and uses @app.route, so "app" has
#                   to exist first, which is why these imports are at the
#                   bottom and not at the top.
#              app/redirect.py is imported LAST on purpose. Its /<code> route
#              catches any single word path, so every fixed page (/, /index,
#              /switch/<id>, later /login) is registered before it.
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import Flask  # The Web Framework's App Class

from app.config import load_config  # Reads .env + Environment Into A Dict

# ----------------------------------------------------------------------------
# App Setup
# ----------------------------------------------------------------------------
app = Flask(__name__)  # __name__ = "app", Flask Uses It To Find The Package's Files
app.config.update(load_config())  # MySQL Settings + Secret Key

from app import db  # noqa: E402  Needs "app" To Exist Before It Is Hooked In
db.init_app(app)  # MySQL Connection + "flask init-db" Command

# Route Modules: Importing Them Is What Registers Their @app.route Functions
from app import routes  # noqa: E402  Imported Last So Routes Can Use "app"
from app import accounts  # noqa: E402  Switch User (URL-12)
from app import redirect  # noqa: E402  /<code> Short Links (URL-11), Kept Last
