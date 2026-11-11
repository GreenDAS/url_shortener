# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/routes.py
# Version: V1.1
# Description: URL routes for the app. Only the placeholder home page so far.
#
#              The real home page (URL-15) will replace index() with a
#              Jinja template listing the signed in user's links. Imported
#              by app/__init__.py after the app is set up, and before
#              app/redirect.py so "/index" is a page, not a short code.
#              Spec sheet: docs/specs/home-page.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from app import app  # The Flask Object, For @app.route

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/")  # Site Root (url.short.com/)
@app.route("/index")  # Same Page Under A Second Name
def index():
    """
    Placeholder home page. Both / and /index run this function.
    Returns: plain text "Hello, World!" with status 200
    """
    return "Hello, World!"
