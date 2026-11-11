# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/accounts.py
# Version: V1.0
# Description: User swapping (URL-12). The browser's session remembers every
#              account that logged in on it, so the header can jump between
#              them without typing the password again. This is not the login
#              check itself, that is users.verify_user() for URL-13.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect, session

from app import app
from app.users import get_user_by_id

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
# Flask's session is a signed cookie, so a user can read these ids but can't
# add someone else's id without the SECRET_KEY.
ACCOUNTS_KEY = "account_ids"  # Session Key: List Of Signed In User Ids
ACTIVE_KEY = "user_id"  # Session Key: The One Being Used Right Now
MAX_ACCOUNTS = 5  # Keeps The Session Cookie Small

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def signed_in_ids():
    """
    Gets every account that is signed in on this browser.
    Returns: list of user ids, most recently used first
    """
    return list(session.get(ACCOUNTS_KEY, []))


def add_account(user_id):
    """
    Remembers an account after it logs in and makes it the active one. The
    login route (URL-13) calls this once verify_user() says the password is right.
    Arg1 = user_id, the users.id that just logged in
    Returns: Nothing
    """
    ids = [i for i in signed_in_ids() if i != user_id]  # Remove So It Can Move To The Front
    ids.insert(0, user_id)
    session[ACCOUNTS_KEY] = ids[:MAX_ACCOUNTS]  # Oldest Falls Off Past MAX_ACCOUNTS
    session[ACTIVE_KEY] = user_id


def switch_to(user_id):
    """
    Makes another signed in account the active one.
    Arg1 = user_id, the account to swap to
    Returns: True if swapped, False if that account never logged in here
    """
    if user_id not in signed_in_ids():
        return False  # Only Accounts That Already Typed Their Password
    add_account(user_id)
    return True


def remove_active_account():
    """
    Logs out only the active account. If others are still signed in, the most
    recent one becomes active.
    Returns: the new active user id, or None if nobody is left
    """
    ids = [i for i in signed_in_ids() if i != session.get(ACTIVE_KEY)]
    session[ACCOUNTS_KEY] = ids
    if ids:
        session[ACTIVE_KEY] = ids[0]
        return ids[0]
    session.pop(ACTIVE_KEY, None)
    return None


def current_user_id():
    """
    Gets the active account.
    Returns: users.id of the active account, or None if nobody is signed in
    """
    return session.get(ACTIVE_KEY)


def switch_choices():
    """
    Builds the list the header's "Switch user" menu shows.
    Returns: list of dicts with id, username and active (True for the current one)
    """
    choices = []
    for user_id in signed_in_ids():
        user = get_user_by_id(user_id)
        if user is not None:  # Skip Accounts Deleted Since They Logged In
            choices.append({"id": user_id, "username": user["username"],
                            "active": user_id == current_user_id()})
    return choices

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/switch/<int:user_id>", methods=["POST"])
def switch_user(user_id):
    """
    The header's "Switch user" menu posts here. POST only, so a link someone
    sends you can't swap your account.
    Arg1 = user_id, the account to swap to
    Returns: redirect to the main page. If that account never signed in here: 403
    """
    if not switch_to(user_id):
        abort(403)
    return redirect("/")  # Fixed Target, Not The Referer, So It Can't Bounce To Another Site
