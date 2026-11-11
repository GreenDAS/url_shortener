# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/redirect.py
# Version: V1.0
# Description: The short link route (URL-11). Visiting /<code> sends the
#              browser to the saved long URL with a 302 and counts the click.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect

from app import app
from app.urls import get_url_by_code, record_click

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REDIRECT_STATUS = 302  # Temporary Redirect, So Browsers Don't Cache It And Clicks Keep Counting

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/<code>")
def follow_short_link(code):
    """
    Sends a short link visitor to the real page. Flask checks its fixed routes
    (like /login) before this one, so a reserved page always wins.
    Arg1 = code, the part after the domain (url.short.com/<code>)
    Returns: 302 redirect to the long URL. If the code is unknown: 404
    """
    link = get_url_by_code(code)
    if link is None:
        abort(404)
    record_click(code)  # Count The Visit Before Leaving The Site
    return redirect(link["long_url"], code=REDIRECT_STATUS)
