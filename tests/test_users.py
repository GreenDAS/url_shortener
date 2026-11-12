# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_users.py
# Version: V1.2
# Description: Unit tests for app/users.py. get_db() is replaced with a mock
#              so no MySQL server is needed.
#
#              get_db() is mocked with a fake connection and cursor, so tests
#              check the SQL sent, that no password is stored (URL-23),
#              duplicate username handling, and that list_users() sorts.
#              Run just this file: python -m unittest tests.test_users -v
#              Spec sheet: docs/specs/users.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

import pymysql

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
    """Checks the username rules."""

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


class TestCreateUser(UsersTestCase):
    """Checks create_user() saves just the username and handles duplicates."""

    def test_returns_new_id_and_commits(self):
        """The new row's id comes back and the insert is committed."""
        self.cursor.lastrowid = 7
        self.assertEqual(users.create_user("dan"), 7)
        self.db.commit.assert_called_once()

    def test_insert_sends_only_the_username(self):
        """The INSERT names only the username column, no password of any kind."""
        users.create_user("dan")
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT INTO users (username)", sql)
        self.assertNotIn("password", sql)
        self.assertEqual(params, ("dan",))

    def test_duplicate_username_raises_user_error(self):
        """A UNIQUE clash becomes UserError and the insert is rolled back."""
        self.cursor.execute.side_effect = pymysql.err.IntegrityError(1062, "Duplicate entry")
        with self.assertRaises(users.UserError):
            users.create_user("dan")
        self.db.rollback.assert_called_once()

    def test_invalid_input_never_touches_db(self):
        """A bad username is caught before any SQL runs."""
        with self.assertRaises(users.UserError):
            users.create_user("x")
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

    def test_no_lookup_selects_a_password(self):
        """Neither lookup asks MySQL for a password column (URL-23)."""
        users.get_user_by_id(1)
        self.assertNotIn("password", self.cursor.execute.call_args.args[0])
        users.get_user_by_username("dan")
        self.assertNotIn("password", self.cursor.execute.call_args.args[0])


class TestListUsers(UsersTestCase):
    """Checks list_users() for the user picker."""

    def test_returns_rows_as_a_list(self):
        """fetchall()'s rows come back as a plain list, in the order MySQL gave."""
        rows = ({"id": 2, "username": "amy"}, {"id": 1, "username": "dan"})
        self.cursor.fetchall.return_value = rows
        self.assertEqual(users.list_users(), list(rows))

    def test_sorted_by_username_in_sql(self):
        """The SELECT sorts by username so the picker order never changes."""
        self.cursor.fetchall.return_value = ()
        users.list_users()
        self.assertIn("ORDER BY username", self.cursor.execute.call_args.args[0])

    def test_no_users_gives_empty_list(self):
        """An empty table gives [] instead of None or a tuple."""
        self.cursor.fetchall.return_value = ()
        self.assertEqual(users.list_users(), [])


class TestSchema(unittest.TestCase):
    """Checks app/schema.sql no longer has a password column."""

    def test_schema_has_no_password_column(self):
        """The users table definition has no password_hash column (URL-23)."""
        from pathlib import Path
        schema = Path(users.__file__).with_name("schema.sql").read_text(encoding="utf-8")
        self.assertNotIn("password_hash VARCHAR", schema)


if __name__ == "__main__":
    unittest.main()
