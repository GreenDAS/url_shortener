# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: url_shortener.py
# Version: V1.1
# Description: Entry point. Gunicorn loads "url_shortener:app", and running
#              this file directly starts the Flask dev server (spec PRE-4).
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from app import app

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)  # Dev Server Only, Not For The Demo
