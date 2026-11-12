# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/urls.py
# Version: V1.2
# Description: Functions for the urls table (URL-10). Makes short codes,
#              saves links, looks them up for the redirect (URL-11) and lists
#              or deletes a user's links for the home page (URL-15).
#
#              Nothing in here is a route, these are helpers the pages call.
#              Who uses what:
#                create_url()          -> create page / API (URL-14)
#                get_url_by_code()     -> app/redirect.py (URL-11)
#                list_urls_for_user()  -> home page (URL-15)
#                delete_url()          -> home page delete button (URL-15)
#              A short code is either random (generate_code) or a custom
#              alias the user picks. Both go in the same "code" column, which
#              is UNIQUE and case sensitive (utf8mb4_bin) in schema.sql.
#              Spec sheet: docs/specs/urls.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import re  # Regular Expressions For The Alias Rule
import secrets  # Random Numbers That Are Safe For Things People Shouldn't Guess
import string  # Ready Made Letter And Digit Lists

import pymysql  # Only Needed For Its IntegrityError (Code Already Used)

from app.db import get_db  # The Request's MySQL Connection

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
CODE_LENGTH = 6  # 62^6 = About 56 Billion Possible Codes
CODE_ALPHABET = string.ascii_letters + string.digits  # a-z, A-Z, 0-9 = 62 Characters
MAX_CODE_TRIES = 5  # Random Clashes Are Rare, Give Up After This Many
MAX_URL_LENGTH = 2048  # Matches VARCHAR(2048) In schema.sql
ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")  # Custom Alias: 3-32 Letters, Numbers, "_" Or "-"

# Codes That Would Clash With The App's Own Pages, Since Short Links Live At /<code>
RESERVED_CODES = {"login", "logout", "home", "api", "static", "admin", "favicon.ico", "index"}

URL_COLUMNS = "id, user_id, code, long_url, created_at"  # Same Columns For Every SELECT

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UrlError(ValueError):
    """
    Raised when a long URL or alias is not allowed. The message is written
    for the user, so a page can show str(error) as is.
    """


class AliasTakenError(UrlError):
    """
    Raised when a custom alias is already used by another link. It is a
    UrlError too, so "except UrlError" catches both.
    """

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def validate_long_url(long_url):
    """
    Checks the link being shortened looks like a web address. The http(s)
    rule also blocks things like "javascript:" links, which a redirect
    should never send anyone to.
    Arg1 = long_url, the full URL the user pasted
    Returns: Nothing. Raises UrlError if it is not http(s), too long or has spaces
    """
    if not isinstance(long_url, str) or not long_url.startswith(("http://", "https://")):
        raise UrlError("URL must start with http:// or https://")
    if len(long_url) > MAX_URL_LENGTH:  # Would Not Fit In The Column
        raise UrlError(f"URL must be at most {MAX_URL_LENGTH} characters.")
    if any(c.isspace() for c in long_url):  # Spaces, Tabs Or Newlines Anywhere
        raise UrlError("URL can't contain spaces.")


def validate_alias(alias):
    """
    Checks a custom short code follows the rules: 3 to 32 letters, numbers,
    "_" or "-", and not one of the site's own page names (RESERVED_CODES,
    checked without caring about upper or lower case).
    Arg1 = alias, the code the user asked for
    Returns: Nothing. Raises UrlError if the format is wrong or it is reserved
    """
    if not isinstance(alias, str) or not ALIAS_PATTERN.match(alias):
        raise UrlError("Alias must be 3-32 letters, numbers, '_' or '-'.")
    if alias.lower() in RESERVED_CODES:  # "Login" Is Blocked As Well As "login"
        raise UrlError(f"'{alias}' is reserved by the site.")


def generate_code():
    """
    Makes a random short code. Uses "secrets" instead of "random" so codes
    can't be predicted from earlier ones. Note: the result is NOT checked
    against RESERVED_CODES. Two of them ("logout", "static") are 6 letters,
    so in theory one could come up (about 2 in 56 billion per link).
    Returns: string of CODE_LENGTH letters and numbers
    """
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))  # Pick 6 Characters


def _insert(user_id, code, long_url):
    """
    Saves one link row. Internal helper for create_url(), the leading "_"
    means other files shouldn't call it.
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
                (user_id, code, long_url),  # %s Placeholders Stop SQL Injection
            )
            row_id = cursor.lastrowid  # The AUTO_INCREMENT id MySQL Just Picked
        db.commit()
    except pymysql.err.IntegrityError:
        db.rollback()  # Undo The Failed Insert So The Connection Is Clean
        raise  # Let create_url() Decide What It Means
    return row_id


def create_url(user_id, long_url, alias=None):
    """
    Shortens a link for a user.

    Steps:
      1. Check the long URL (raises UrlError).
      2. With an alias: check it, try to save it once. If MySQL says the
         code already exists, raise AliasTakenError.
      3. Without an alias: make a random code and try to save it. If that
         random code happens to be taken, make a new one and try again, up
         to MAX_CODE_TRIES times, then give up with UrlError.
      4. Read the saved row back so the caller gets id and created_at too.
    MySQL's UNIQUE rule on urls.code is what catches clashes, so two people
    asking for the same alias at once can't both get it.

    Arg1 = user_id, the owner's users.id
    Arg2 = long_url, the full URL to shorten
    Arg3 = alias, optional custom code (None or "" = make a random one)
    Returns: the new link as a dict (see get_url_by_code)
    Raises: UrlError for bad input, AliasTakenError if the alias is used
    """
    validate_long_url(long_url)

    if alias:  # Custom Alias Path
        validate_alias(alias)
        try:
            _insert(user_id, alias, long_url)
        except pymysql.err.IntegrityError:
            raise AliasTakenError(f"'{alias}' is already taken.")
        return get_url_by_code(alias)

    for _ in range(MAX_CODE_TRIES):  # Random Code Path
        code = generate_code()
        try:
            _insert(user_id, code, long_url)
            return get_url_by_code(code)
        except pymysql.err.IntegrityError:
            continue  # Random Code Clashed, Try Another One
    raise UrlError("Couldn't make a unique short code, please try again.")


def get_url_by_code(code):
    """
    Looks up a link by its short code (used by the redirect). The match is
    case sensitive because of the utf8mb4_bin collation on the column.
    Arg1 = code, the part after the domain
    Returns: dict with id, user_id, code, long_url, created_at. If not found: None
    """
    with get_db().cursor() as cursor:
        cursor.execute(f"SELECT {URL_COLUMNS} FROM urls WHERE code = %s", (code,))  # f-string Only Adds Our Own Column List
        return cursor.fetchone()  # DictCursor: One Row As A Dict, Or None


def list_urls_for_user(user_id):
    """
    Gets every link a user owns for their home page.
    Arg1 = user_id, the owner's users.id
    Returns: list of link dicts, newest first (empty list if they have none)
    """
    with get_db().cursor() as cursor:
        cursor.execute(
            f"SELECT {URL_COLUMNS} FROM urls WHERE user_id = %s ORDER BY created_at DESC, id DESC",  # id Breaks Ties In The Same Second
            (user_id,),
        )
        return list(cursor.fetchall())  # Plain List, Not A Tuple


def delete_url(user_id, code):
    """
    Removes one of a user's links. The owner check is part of the DELETE
    itself, so nobody can delete someone else's link by guessing its code.
    Arg1 = user_id, the users.id of whoever is asking
    Arg2 = code, the short code to remove
    Returns: True if a link was deleted, False if it doesn't exist or isn't theirs
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM urls WHERE code = %s AND user_id = %s", (code, user_id))  # Owner Check In The SQL
        deleted = cursor.rowcount == 1  # rowcount = How Many Rows MySQL Removed
    db.commit()
    return deleted

