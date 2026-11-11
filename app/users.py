# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/users.py
# Version: V1.0
# Description: Functions for the users table (URL-9). Creates accounts, looks
#              them up and checks passwords for the login page (URL-13).
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import re

import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,50}$")  # 3-50 Letters, Numbers, "_" Or "-"
MIN_PASSWORD_LENGTH = 8

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UserError(ValueError):
    """Raised when a username or password is not allowed, or is already taken."""

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def validate_username(username):
    """
    Checks a username follows the rules.
    Arg1 = username, the name the user typed
    Returns: Nothing. Raises UserError if it is not allowed
    """
    if not isinstance(username, str) or not USERNAME_PATTERN.match(username):
        raise UserError("Username must be 3-50 letters, numbers, '_' or '-'.")


def validate_password(password):
    """
    Checks a password is long enough.
    Arg1 = password, the plain text password the user typed
    Returns: Nothing. Raises UserError if it is too short
    """
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise UserError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")


def create_user(username, password):
    """
    Adds a new account to the users table.
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
            user_id = cursor.lastrowid
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()  # UNIQUE On username Failed
        raise UserError(f"Username '{username}' is already taken.")
    return user_id


def get_user_by_username(username):
    """
    Looks up one account by its login name.
    Arg1 = username, the login name
    Returns: dict with id, username, password_hash, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = %s",
            (username,),
        )
        return cursor.fetchone()


def get_user_by_id(user_id):
    """
    Looks up one account by its id (what the login session stores).
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
    Arg1 = username, the login name typed in
    Arg2 = password, the plain text password typed in
    Returns: the user dict (without password_hash) if they match, Else: None
    """
    user = get_user_by_username(username)
    if user is None or not check_password_hash(user["password_hash"], password):
        return None  # Same Answer For "No Such User" And "Wrong Password"
    user = dict(user)
    user.pop("password_hash")  # Never Hand The Hash Back To Callers
    return user
