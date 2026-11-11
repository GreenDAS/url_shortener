# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/users.py
# Version: V1.1
# Description: Functions for the users table (URL-9). Creates accounts, looks
#              them up and checks passwords for the login page (URL-13).
#
#              Nothing in here is a route, these are helpers the pages call.
#              Who uses what:
#                create_user()     -> sign up page (later)
#                verify_user()     -> login page (URL-13)
#                get_user_by_id()  -> app/accounts.py "Switch user" menu
#              Passwords are only ever stored as a werkzeug salted hash, and
#              every query uses %s placeholders so typed input can't change
#              the SQL (no SQL injection).
#              Spec sheet: docs/specs/users.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import re  # Regular Expressions For The Username Rule

import pymysql  # Only Needed For Its IntegrityError (Duplicate Username)
from werkzeug.security import check_password_hash, generate_password_hash  # Comes With Flask

from app.db import get_db  # The Request's MySQL Connection

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,50}$")  # 3-50 Letters, Numbers, "_" Or "-"
MIN_PASSWORD_LENGTH = 8  # Shortest Password Allowed

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UserError(ValueError):
    """
    Raised when a username or password is not allowed, or is already taken.
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


def validate_password(password):
    """
    Checks a password is long enough (at least MIN_PASSWORD_LENGTH characters).
    There is no upper limit since only the fixed size hash is stored.
    Arg1 = password, the plain text password the user typed
    Returns: Nothing. Raises UserError if it is too short
    """
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise UserError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


def create_user(username, password):
    """
    Adds a new account to the users table.

    Steps:
      1. Check the username and password rules (raises UserError).
      2. Hash the password and INSERT the row.
      3. Commit. If MySQL says the username already exists (the UNIQUE
         rule on users.username), roll back and raise UserError instead.
    Letting MySQL catch duplicates, instead of looking first, means two
    sign ups with the same name at the same moment can't both get through.

    Arg1 = username, the login name (must be unique)
    Arg2 = password, the plain text password (only its hash gets saved)
    Returns: the new user's id. Raises UserError if invalid or already taken
    """
    validate_username(username)
    validate_password(password)

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password)),  # %s Placeholders Stop SQL Injection
            )
            user_id = cursor.lastrowid  # The AUTO_INCREMENT id MySQL Just Picked
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()  # UNIQUE On username Failed
        raise UserError(f"Username '{username}' is already taken.")
    return user_id


def get_user_by_username(username):
    """
    Looks up one account by its login name. This one includes the
    password_hash because verify_user() needs it, so don't send its result
    to a page.
    Arg1 = username, the login name
    Returns: dict with id, username, password_hash, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = %s",
            (username,),  # One Item Tuple, The Comma Matters
        )
        return cursor.fetchone()  # DictCursor: One Row As A Dict, Or None


def get_user_by_id(user_id):
    """
    Looks up one account by its id (what the login session stores). Leaves
    out password_hash, so the result is safe to show on a page.
    Arg1 = user_id, the users.id value
    Returns: dict with id, username, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT id, username, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def verify_user(username, password):
    """
    Checks a username and password for logging in.

    Steps:
      1. Look the account up by username.
      2. If it exists, have werkzeug hash the typed password the same way
         and compare it with the stored hash.
      3. On a match, hand back a copy of the row with password_hash removed.
    Arg1 = username, the login name typed in
    Arg2 = password, the plain text password typed in
    Returns: the user dict (without password_hash) if they match, Else: None
    """
    user = get_user_by_username(username)
    if user is None or not check_password_hash(user["password_hash"], password):
        return None  # Same Answer For "No Such User" And "Wrong Password"
    user = dict(user)  # Copy, So The Original Row Isn't Changed
    user.pop("password_hash")  # Never Hand The Hash Back To Callers
    return user
