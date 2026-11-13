# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/accounts.py
# Version: V1.2
# Description: User swapping (URL-12). The browser's session remembers which
#              user is the current one, and a "Switch user" control can change
#              it to any user that exists. There are no passwords and no
#              login, the class only asks for swapping (URL-23, URL-24).
#
#              What the session holds (Flask's signed cookie):
#                session["user_id"] = 7    the current user's users.id
#              How the pieces fit:
#                user picker / menu  -> switch_choices() builds the list
#                picking a user      -> POST /switch/<id> -> switch_to(id)
#                any page            -> current_user_id() says who is current
#              Spec sheet: docs/specs/user-swap.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect, session  # session = The Signed Cookie As A Dict

from app import app  # The Flask Object, For @app.route
from app.users import get_user_by_id, list_users  # users Table Helpers (URL-9)

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
ACTIVE_KEY = "user_id"  # Session Key: The User Being Used Right Now

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def current_user_id():
    """
    Gets the current user.
    Returns: users.id of the current user, or None if nobody has been picked yet
    """
    return session.get(ACTIVE_KEY)


def switch_to(user_id):
    """
    Makes a user the current one. Any user in the users table can be
    switched to, since there are no passwords to check.
    Arg1 = user_id, the users.id to swap to
    Returns: True if swapped, False if no user has that id (nothing changes)
    """
    if get_user_by_id(user_id) is None:
        return False  # No Such User, Leave The Session Alone
    session[ACTIVE_KEY] = user_id
    return True


def switch_choices():
    """
    Builds the list the "Switch user" control shows: every user from
    list_users(), with the current one marked.
    Returns: list of dicts with id, username and active (True for the current user)
    """
    active_id = current_user_id()  # Read Once, Not Once Per User
    return [{"id": user["id"], "username": user["username"], "active": user["id"] == active_id}
            for user in list_users()]  # Keeps list_users()'s A To Z Order

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/switch/<int:user_id>", methods=["POST"])  # <int:...> Means /switch/abc Is A 404
def switch_user(user_id):
    """
    The "Switch user" control posts here. POST only, so a link someone sends
    you can't swap your user.
    Arg1 = user_id, the user to swap to
    Returns: redirect to the main page. If no user has that id: 404
    """
    if not switch_to(user_id):
        abort(404)  # Not Found: No User With That id
    return redirect("/")  # Fixed Target, Not The Referer, So It Can't Bounce To Another Site
