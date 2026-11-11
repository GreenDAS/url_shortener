# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/accounts.py
# Version: V1.1
# Description: User swapping (URL-12). The browser's session remembers every
#              account that logged in on it, so the header can jump between
#              them without typing the password again. This is not the login
#              check itself, that is users.verify_user() for URL-13.
#
#              What the session holds (Flask's signed cookie):
#                session["account_ids"] = [7, 3, 12]  every signed in id,
#                                         most recently used first, max 5
#                session["user_id"]     = 7           the active account
#              How the pieces fit:
#                login (URL-13)  -> add_account(id) after the password is right
#                header menu     -> switch_choices() builds the list
#                menu click      -> POST /switch/<id> -> switch_to(id)
#                logout          -> remove_active_account()
#                any page        -> current_user_id() says who is active
#              Spec sheet: docs/specs/user-swap.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from flask import abort, redirect, session  # session = The Signed Cookie As A Dict

from app import app  # The Flask Object, For @app.route
from app.users import get_user_by_id  # Turns An id Into A Username For The Menu

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
    Gets every account that is signed in on this browser. Hands back a copy,
    so changing the list doesn't change the session until it is saved back.
    Returns: list of user ids, most recently used first (empty if none)
    """
    return list(session.get(ACCOUNTS_KEY, []))  # list() Makes The Copy


def add_account(user_id):
    """
    Remembers an account after it logs in and makes it the active one. The
    login route (URL-13) calls this once verify_user() says the password is right.

    Steps:
      1. Take the id out of the list if it is already there.
      2. Put it at the front (most recently used).
      3. Keep only the first MAX_ACCOUNTS, so the oldest falls off.
      4. Mark it as the active account.
    switch_to() reuses this, which is how a swap also moves that account
    to the front of the list.

    Arg1 = user_id, the users.id that just logged in
    Returns: Nothing
    """
    ids = [i for i in signed_in_ids() if i != user_id]  # Remove So It Can Move To The Front
    ids.insert(0, user_id)
    session[ACCOUNTS_KEY] = ids[:MAX_ACCOUNTS]  # Oldest Falls Off Past MAX_ACCOUNTS
    session[ACTIVE_KEY] = user_id


def switch_to(user_id):
    """
    Makes another signed in account the active one. Only ids already in the
    list work, which is what makes skipping the password safe: that account
    already typed it on this browser.
    Arg1 = user_id, the account to swap to
    Returns: True if swapped, False if that account never logged in here
    """
    if user_id not in signed_in_ids():
        return False  # Only Accounts That Already Typed Their Password
    add_account(user_id)  # Moves It To The Front And Makes It Active
    return True


def remove_active_account():
    """
    Logs out only the active account. If others are still signed in, the most
    recent one becomes active.
    Returns: the new active user id, or None if nobody is left
    """
    ids = [i for i in signed_in_ids() if i != session.get(ACTIVE_KEY)]  # Everyone But The Active One
    session[ACCOUNTS_KEY] = ids
    if ids:
        session[ACTIVE_KEY] = ids[0]  # Next Most Recent Takes Over
        return ids[0]
    session.pop(ACTIVE_KEY, None)  # Nobody Left, Fully Logged Out
    return None


def current_user_id():
    """
    Gets the active account.
    Returns: users.id of the active account, or None if nobody is signed in
    """
    return session.get(ACTIVE_KEY)


def switch_choices():
    """
    Builds the list the header's "Switch user" menu shows. Looks each id up
    in the users table to get its username, and skips any account that has
    been deleted since it signed in.
    Returns: list of dicts with id, username and active (True for the current one)
    """
    choices = []
    for user_id in signed_in_ids():  # Keeps Most Recently Used First
        user = get_user_by_id(user_id)
        if user is not None:  # Skip Accounts Deleted Since They Logged In
            choices.append({"id": user_id, "username": user["username"],
                            "active": user_id == current_user_id()})
    return choices

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route("/switch/<int:user_id>", methods=["POST"])  # <int:...> Means /switch/abc Is A 404
def switch_user(user_id):
    """
    The header's "Switch user" menu posts here. POST only, so a link someone
    sends you can't swap your account.
    Arg1 = user_id, the account to swap to
    Returns: redirect to the main page. If that account never signed in here: 403
    """
    if not switch_to(user_id):
        abort(403)  # Forbidden: Not One Of This Browser's Accounts
    return redirect("/")  # Fixed Target, Not The Referer, So It Can't Bounce To Another Site
