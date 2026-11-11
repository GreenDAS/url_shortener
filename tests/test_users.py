# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: tests/test_users.py
# Version: V1.0
# Description: Unit tests for app/users.py. get_db() is replaced with a mock
#              so no MySQL server is needed.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

from url_shortener import app
from app import users

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UsersTestCase(unittest.TestCase):
    """Base class: swaps get_db() for a fake connection with a fake cursor."""

    def setUp(self):
        """Patches app.users.get_db and opens an app context."""
        patcher = mock.patch("app.users.get_db")
        self.get_db = patcher.start()
        self.addCleanup(patcher.stop)
        self.db = self.get_db.return_value
        self.cursor = self.db.cursor.return_value.__enter__.return_value  # What "with db.cursor() as c" Gives
        context = app.app_context()
        context.push()
        self.addCleanup(context.pop)


class TestValidation(unittest.TestCase):
    """Checks the username and password rules."""

    def test_good_username_passes(self):
        """Letters, numbers, "_" and "-" are allowed."""
        users.validate_username("dan_s-203")  # No Exception = Pass

    def test_short_username_fails(self):
        """Under 3 characters is rejected."""
        with self.assertRaises(users.UserError):
            users.validate_username("ab")

    def test_username_with_space_fails(self):
        """Spaces and symbols are rejected."""
        with self.assertRaises(users.UserError):
            users.validate_username("dan s")

    def test_non_string_username_fails(self):
        """None is rejected instead of crashing."""
        with self.assertRaises(users.UserError):
            users.validate_username(None)

    def test_short_password_fails(self):
        """Passwords under MIN_PASSWORD_LENGTH are rejected."""
        with self.assertRaises(users.UserError):
            users.validate_password("short")

    def test_long_enough_password_passes(self):
        """A password of exactly the minimum length is allowed."""
        users.validate_password("x" * users.MIN_PASSWORD_LENGTH)


class TestCreateUser(UsersTestCase):
    """Checks create_user() saves a hashed password and handles duplicates."""

    def test_returns_new_id_and_commits(self):
        """The new row's id comes back and the insert is committed."""
        self.cursor.lastrowid = 7
        self.assertEqual(users.create_user("dan", "password123"), 7)
        self.db.commit.assert_called_once()

    def test_password_is_hashed_not_plain(self):
        """The value sent to MySQL is a hash that matches, not the password itself."""
        users.create_user("dan", "password123")
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO users", sql)
        self.assertEqual(params[0], "dan")
        self.assertNotEqual(params[1], "password123")
        self.assertTrue(check_password_hash(params[1], "password123"))

    def test_duplicate_username_raises_user_error(self):
        """A UNIQUE clash becomes UserError and the insert is rolled back."""
        self.cursor.execute.side_effect = pymysql.err.IntegrityError(1062, "Duplicate entry")
        with self.assertRaises(users.UserError):
            users.create_user("dan", "password123")
        self.db.rollback.assert_called_once()

    def test_invalid_input_never_touches_db(self):
        """A bad username is caught before any SQL runs."""
        with self.assertRaises(users.UserError):
            users.create_user("x", "password123")
        self.cursor.execute.assert_not_called()


class TestLookups(UsersTestCase):
    """Checks get_user_by_username() and get_user_by_id()."""

    def test_get_by_username_uses_placeholder(self):
        """The username is passed as a parameter, not pasted into the SQL."""
        self.cursor.fetchone.return_value = {"id": 1, "username": "dan"}
        self.assertEqual(users.get_user_by_username("dan")["id"], 1)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE username = %s", sql)
        self.assertEqual(params, ("dan",))

    def test_get_by_id_missing_returns_none(self):
        """An id with no row gives None."""
        self.cursor.fetchone.return_value = None
        self.assertIsNone(users.get_user_by_id(99))

    def test_get_by_id_never_selects_hash(self):
        """get_user_by_id() does not pull password_hash."""
        users.get_user_by_id(1)
        sql = self.cursor.execute.call_args.args[0]
        self.assertNotIn("password_hash", sql)


class TestVerifyUser(UsersTestCase):
    """Checks verify_user() for logging in."""

    def setUp(self):
        """Fakes a stored user whose password is "password123"."""
        super().setUp()
        self.cursor.fetchone.return_value = {
            "id": 1,
            "username": "dan",
            "password_hash": generate_password_hash("password123"),
            "created_at": None,
        }

    def test_right_password_returns_user_without_hash(self):
        """Correct login gives the user back with password_hash removed."""
        user = users.verify_user("dan", "password123")
        self.assertEqual(user["id"], 1)
        self.assertNotIn("password_hash", user)

    def test_wrong_password_returns_none(self):
        """Wrong password gives None."""
        self.assertIsNone(users.verify_user("dan", "wrong-password"))

    def test_unknown_user_returns_none(self):
        """A username that doesn't exist gives None too."""
        self.cursor.fetchone.return_value = None
        self.assertIsNone(users.verify_user("nobody", "password123"))


if __name__ == "__main__":
    unittest.main()
