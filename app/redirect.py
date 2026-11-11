# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/redirect.py
# Version: V1.1
# Description: The short link route (URL-11). Visiting /<code> sends the
#              browser to the saved long URL with a 302 and counts the click.
#
#              The whole round trip:
#                1. Someone opens url.short.com/aB12cD.
#                2. Apache passes it to Gunicorn, which hands it to Flask.
#                3. Flask has no fixed page called /aB12cD, so it lands in
#                   follow_short_link() with code = "aB12cD".
#                4. app/urls.py looks the code up. Unknown = 404 page.
#                5. Known = add 1 to its clicks, then answer 302 with a
#                   Location header of the long URL. The browser follows it.
#              This file must be imported last in app/__init__.py so every
#              fixed page is matched before this catch all.
#              Spec sheet: docs/specs/redirect.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect  # abort() = Error Page, redirect() = 3xx Response

from app import app  # The Flask Object, For @app.route
from app.urls import get_url_by_code, record_click  # urls Table Helpers (URL-10)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REDIRECT_STATUS = 302  # Temporary Redirect, So Browsers Don't Cache It And Clicks Keep Counting

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/<code>")  # One Path Segment, So /a/b Is Not Caught Here
def follow_short_link(code):
    """
    Sends a short link visitor to the real page. Flask checks its fixed routes
    (like /login) before this one, so a reserved page always wins.
    Arg1 = code, the part after the domain (url.short.com/<code>)
    Returns: 302 redirect to the long URL. If the code is unknown: 404
    """
    link = get_url_by_code(code)  # None If No Row Has This Code
    if link is None:
        abort(404)  # Stops Here, Flask Sends Its Not Found Page
    record_click(code)  # Count The Visit Before Leaving The Site
    return redirect(link["long_url"], code=REDIRECT_STATUS)
