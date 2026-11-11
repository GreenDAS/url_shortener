# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: url_shortener.py
# Version: V1.2
# Description: Entry point. Gunicorn loads "url_shortener:app", and running
#              this file directly starts the Flask dev server (spec PRE-4).
#
#              Three ways this file gets used:
#                1. Gunicorn (the real server, in Docker): gunicorn_config.py
#                   says wsgi_app = "url_shortener:app", so Gunicorn imports
#                   this module and serves its "app" variable.
#                2. "python url_shortener.py": the __main__ block below starts
#                   Flask's built in dev server on 127.0.0.1:5000.
#                3. "flask --app url_shortener init-db" and the unit tests:
#                   they import "app" from here to get the same Flask object.
#              Importing "app" runs app/__init__.py, which does all the setup.
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from app import app  # The Fully Set Up Flask Object From app/__init__.py

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
# Only True When This File Is Run Directly, Not When Gunicorn Imports It
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)  # Dev Server Only, Not For The Demo
