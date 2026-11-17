# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: app/routes.py
# Version: V1.4
# Description: The pages of the site and the forms on them: the home page
#              with the list of the current user's links and their Delete
#              buttons (URL-15), the create short link form with its optional
#              custom alias box (URL-14, URL-22), and the "Add user" box of
#              the user picker (URL-13).
#
#              Every form here is a plain HTML form (no JavaScript). The
#              pattern is always the same:
#                form POSTs -> the route does the work
#                  worked -> redirect back to "/" (so a refresh can't resend)
#                  failed -> show the home page again with the error on it
#              Switching users is not in this file, that is app/accounts.py.
#              Imported by app/__init__.py after the app is set up, and
#              before app/redirect.py so "/index" is a page, not a short code.
#              Spec sheet: docs/specs/home-page.md (the picker: user-picker.md)
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect, render_template, request  # request = The Incoming Form Data

from app import app  # The Flask Object, For @app.route
from app.accounts import current_user_id, switch_choices, switch_to  # Who Is Current + Swapping (URL-12)
from app.urls import UrlError, create_url, delete_url, list_urls_for_user  # urls Table Helpers (URL-10)
from app.users import UserError, create_user, get_user_by_id  # users Table Helpers (URL-9)

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def current_user():
    """
    Gets the current user's row, not just the id the session holds. Also
    covers a stale session: if the remembered user was deleted from the
    table, this returns None and the page asks to pick a user again.
    Returns: dict with id, username, created_at, or None if nobody is picked
    """
    user_id = current_user_id()
    if user_id is None:
        return None  # Nobody Picked Yet, Skip The Database
    return get_user_by_id(user_id)  # None If That User No Longer Exists


def render_home(status=200, **extra):
    """
    Builds the home page. Every route that shows the page goes through
    here, so the header's user picker and the list of links always get the
    same values. The list only ever holds the current user's own links,
    because list_urls_for_user() filters by their id.
    Arg1 = status, the HTTP status to answer with (200, or 400 after a bad form)
    Arg2 = extra, any more values for the template (user_error, typed_username,
           link_error, typed_long_url, typed_alias)
    Returns: (page HTML, status) for Flask to send
    """
    user = current_user()
    page = render_template(
        "home.html",
        user=user,  # None = "Pick Or Add A User" Message
        links=list_urls_for_user(user["id"]) if user else [],  # Newest First, Nothing Without A User
        base_url=request.host_url,  # "http://url.short.com/" Or "http://127.0.0.1:5000/", Whichever Was Typed
        choices=switch_choices(),  # Every User, For The Switch Dropdown
        **extra,
    )
    return page, status

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/")  # Site Root (url.short.com/)
@app.route("/index")  # Same Page Under A Second Name
def index():
    """
    The home page. Both / and /index run this function.
    Returns: the home page with status 200
    """
    return render_home()


@app.route("/users", methods=["POST"])  # POST Only, The "Add user" Box Posts Here
def add_user():
    """
    The "Add user" box of the user picker (URL-13). Creates the user and
    switches to it right away. No password is asked for.
    Form field: username, the name typed in the box
    Returns: redirect to the home page. If the name is bad or taken: the home
             page again with the error on it and status 400
    """
    username = request.form.get("username", "").strip()  # "" If The Field Is Missing, Spaces Trimmed
    try:
        user_id = create_user(username)  # Raises UserError For A Bad Or Taken Name
    except UserError as error:
        return render_home(400, user_error=str(error), typed_username=username)  # 400 = Bad Request
    switch_to(user_id)  # The New User Becomes The Current One
    return redirect("/")


@app.route("/links", methods=["POST"])  # POST Only, The Create Form Posts Here
def create_link():
    """
    The create short link form (URL-14). Shortens the pasted URL for the
    current user. The alias box is optional (URL-22): left empty, a random
    6 character code is made.
    Form field: long_url, the full URL to shorten
    Form field: alias, optional custom short code
    Returns: redirect to the home page, where the new link is the top row.
             If nobody is picked: redirect to the home page, nothing is made.
             If the URL or alias is bad, or the alias is taken: the home page
             again with the error above the form and status 400
    """
    user = current_user()
    if user is None:
        return redirect("/")  # Nobody Picked, The Page Will Ask To Pick A User
    long_url = request.form.get("long_url", "").strip()  # "" If The Field Is Missing, Spaces Trimmed
    alias = request.form.get("alias", "").strip()
    try:
        create_url(user["id"], long_url, alias or None)  # "" Becomes None = Make A Random Code
    except UrlError as error:  # AliasTakenError Is A UrlError Too
        return render_home(400, link_error=str(error), typed_long_url=long_url, typed_alias=alias)
    return redirect("/")


@app.route("/links/<code>/delete", methods=["POST"])  # POST Only, Each Row's Delete Button Posts Here
def delete_link(code):
    """
    The Delete button next to a link (URL-15). Only removes the link if the
    current user owns it, delete_url() checks that inside its SQL.
    Arg1 = code, the short code of the link to remove
    Returns: redirect to the home page. If nobody is picked: redirect to the
             home page without deleting. If the link doesn't exist or belongs
             to another user: 404
    """
    user = current_user()
    if user is None:
        return redirect("/")  # Nobody Picked, The Page Will Ask To Pick A User
    if not delete_url(user["id"], code):
        abort(404)  # Not Found: No Such Link, Or It Is Someone Else's
    return redirect("/")
