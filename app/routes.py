# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: app/routes.py
# Version: V1.2
# Description: The pages of the site and the forms on them. Right now that is
#              the home page and the "Add user" box of the user picker
#              (URL-13).
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
from flask import redirect, render_template, request  # request = The Incoming Form Data

from app import app  # The Flask Object, For @app.route
from app.accounts import current_user_id, switch_choices, switch_to  # Who Is Current + Swapping (URL-12)
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
    here, so the header's user picker always gets the same values.
    Arg1 = status, the HTTP status to answer with (200, or 400 after a bad form)
    Arg2 = extra, any more values for the template (user_error, typed_username)
    Returns: (page HTML, status) for Flask to send
    """
    page = render_template(
        "home.html",
        user=current_user(),  # None = "Pick Or Add A User" Message
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
