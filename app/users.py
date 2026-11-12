# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/users.py
# Version: V1.2
# Description: Functions for the users table (URL-9). A user is just a unique
#              username. There are no passwords, since the class only wants
#              the ability to swap between users, not authentication (URL-23).
#
#              Nothing in here is a route, these are helpers the pages call.
#              Who uses what:
#                create_user()     -> "add user" box on the user picker (URL-13)
#                list_users()      -> user picker / "Switch user" menu
#                get_user_by_id()  -> app/accounts.py, checks a user exists
#              Every query uses %s placeholders so typed input can't change
#              the SQL (no SQL injection).
#              Spec sheet: docs/specs/users.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import re  # Regular Expressions For The Username Rule

import pymysql  # Only Needed For Its IntegrityError (Duplicate Username)

from app.db import get_db  # The Request's MySQL Connection

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,50}$")  # 3-50 Letters, Numbers, "_" Or "-"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UserError(ValueError):
    """
    Raised when a username is not allowed, or is already taken.
    The message is written for the user, so a page can show str(error) as is.
    """

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def validate_username(username):
    """
    Checks a username follows the rules: 3 to 50 characters, only letters,
    numbers, "_" or "-". 50 matches the VARCHAR(50) column in schema.sql.
    Arg1 = username, the name the user typed
    Returns: Nothing. Raises UserError if it is not allowed
    """
    if not isinstance(username, str) or not USERNAME_PATTERN.match(username):  # None Or Numbers Fail Too
        raise UserError("Username must be 3-50 letters, numbers, '_' or '-'.")


def create_user(username):
    """
    Adds a new user to the users table.

    Steps:
      1. Check the username rules (raises UserError).
      2. INSERT the row.
      3. Commit. If MySQL says the username already exists (the UNIQUE
         rule on users.username), roll back and raise UserError instead.
    Letting MySQL catch duplicates, instead of looking first, means two
    people adding the same name at the same moment can't both get through.

    Arg1 = username, the user's name (must be unique)
    Returns: the new user's id. Raises UserError if invalid or already taken
    """
    validate_username(username)

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username) VALUES (%s)",
                (username,),  # %s Placeholder Stops SQL Injection, The Comma Makes It A Tuple
            )
            user_id = cursor.lastrowid  # The AUTO_INCREMENT id MySQL Just Picked
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()  # UNIQUE On username Failed
        raise UserError(f"Username '{username}' is already taken.")
    return user_id


def get_user_by_username(username):
    """
    Looks up one user by name.
    Arg1 = username, the user's name
    Returns: dict with id, username, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT id, username, created_at FROM users WHERE username = %s",
            (username,),  # One Item Tuple, The Comma Matters
        )
        return cursor.fetchone()  # DictCursor: One Row As A Dict, Or None


def get_user_by_id(user_id):
    """
    Looks up one user by id (what the session stores for the current user).
    Arg1 = user_id, the users.id value
    Returns: dict with id, username, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT id, username, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def list_users():
    """
    Gets every user, for the user picker to show as choices.
    Returns: list of dicts with id, username, created_at, sorted by username
             (empty list if there are no users yet)
    """
    with get_db().cursor() as cursor:
        cursor.execute("SELECT id, username, created_at FROM users ORDER BY username")  # A To Z
        return list(cursor.fetchall())  # Plain List, Not A Tuple
