# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/urls.py
# Version: V1.0
# Description: Functions for the urls table (URL-10). Makes short codes,
#              saves links, looks them up for the redirect (URL-11) and lists
#              or deletes a user's links for the home page (URL-15).
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import re
import secrets
import string

import pymysql

from app.db import get_db

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
CODE_LENGTH = 6  # 62^6 = About 56 Billion Possible Codes
CODE_ALPHABET = string.ascii_letters + string.digits
MAX_CODE_TRIES = 5  # Random Clashes Are Rare, Give Up After This Many
MAX_URL_LENGTH = 2048
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")  # Custom Alias: 3-32 Letters, Numbers, "_" Or "-"

# Codes That Would Clash With The App's Own Pages, Since Short Links Live At /<code>
RESERVED_CODES = {"login", "logout", "home", "api", "static", "admin", "favicon.ico", "index"}

URL_COLUMNS = "id, user_id, code, long_url, clicks, created_at"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UrlError(ValueError):
    """Raised when a long URL or alias is not allowed."""


class AliasTakenError(UrlError):
    """Raised when a custom alias is already used by another link."""

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def validate_long_url(long_url):
    """
    Checks the link being shortened looks like a web address.
    Arg1 = long_url, the full URL the user pasted
    Returns: Nothing. Raises UrlError if it is not http(s) or too long
    """
    if not isinstance(long_url, str) or not long_url.startswith(("http://", "https://")):
        raise UrlError("URL must start with http:// or https://")
    if len(long_url) > MAX_URL_LENGTH:
        raise UrlError(f"URL must be at most {MAX_URL_LENGTH} characters.")
    if any(c.isspace() for c in long_url):
        raise UrlError("URL can't contain spaces.")


def validate_alias(alias):
    """
    Checks a custom short code follows the rules.
    Arg1 = alias, the code the user asked for
    Returns: Nothing. Raises UrlError if the format is wrong or it is reserved
    """
    if not isinstance(alias, str) or not ALIAS_PATTERN.match(alias):
        raise UrlError("Alias must be 3-32 letters, numbers, '_' or '-'.")
    if alias.lower() in RESERVED_CODES:
        raise UrlError(f"'{alias}' is reserved by the site.")


def generate_code():
    """
    Makes a random short code.
    Returns: string of CODE_LENGTH letters and numbers
    """
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _insert(user_id, code, long_url):
    """
    Saves one link row.
    Arg1 = user_id, the owner's users.id
    Arg2 = code, the short code
    Arg3 = long_url, the full URL
    Returns: the new row's id. Raises pymysql IntegrityError if the code is taken
    """
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO urls (user_id, code, long_url) VALUES (%s, %s, %s)",
                (user_id, code, long_url),
            )
            row_id = cursor.lastrowid
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()
        raise
    return row_id


def create_url(user_id, long_url, alias=None):
    """
    Shortens a link for a user.
    Arg1 = user_id, the owner's users.id
    Arg2 = long_url, the full URL to shorten
    Arg3 = alias, optional custom code (None = make a random one)
    Returns: the new link as a dict (see get_url_by_code)
    Raises: UrlError for bad input, AliasTakenError if the alias is used
    """
    validate_long_url(long_url)

    if alias:
        validate_alias(alias)
        try:
            _insert(user_id, alias, long_url)
        except pymysql.err.IntegrityError:
            raise AliasTakenError(f"'{alias}' is already taken.")
        return get_url_by_code(alias)

    for _ in range(MAX_CODE_TRIES):
        code = generate_code()
        try:
            _insert(user_id, code, long_url)
            return get_url_by_code(code)
        except pymysql.err.IntegrityError:
            continue  # Random Code Clashed, Try Another One
    raise UrlError("Couldn't make a unique short code, please try again.")


def get_url_by_code(code):
    """
    Looks up a link by its short code (used by the redirect).
    Arg1 = code, the part after the domain
    Returns: dict with id, user_id, code, long_url, clicks, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(f"SELECT {URL_COLUMNS} FROM urls WHERE code = %s", (code,))
        return cursor.fetchone()


def list_urls_for_user(user_id):
    """
    Gets every link a user owns for their home page.
    Arg1 = user_id, the owner's users.id
    Returns: list of link dicts, newest first
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            f"SELECT {URL_COLUMNS} FROM urls WHERE user_id = %s ORDER BY created_at DESC, id DESC",
            (user_id,),
        )
        return list(cursor.fetchall())


def delete_url(user_id, code):
    """
    Removes one of a user's links.
    Arg1 = user_id, the users.id of whoever is asking
    Arg2 = code, the short code to remove
    Returns: True if a link was deleted, False if it doesn't exist or isn't theirs
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM urls WHERE code = %s AND user_id = %s", (code, user_id))  # Owner Check In The SQL
        deleted = cursor.rowcount == 1
    db.commit()
    return deleted


def record_click(code):
    """
    Adds 1 to a link's click counter when someone uses it.
    Arg1 = code, the short code that was visited
    Returns: True if the link exists, Else: False
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE code = %s", (code,))  # Done In SQL So Two Clicks Can't Overwrite Each Other
        found = cursor.rowcount == 1
    db.commit()
    return found
