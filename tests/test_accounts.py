# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_accounts.py
# Version: V1.1
# Description: Unit tests for app/accounts.py (URL-12 user swapping). Uses a
#              test request so there is a real session, and mocks the users
#              table so no MySQL server is needed.
#
#              Runs each test inside app.test_request_context() so the session
#              works without a browser. get_user_by_id is mocked so no MySQL
#              is needed. Covers add/switch/remove, the 5 account cap, the
#              menu list and the POST /switch/<id> route (403 + redirect).
#              Run just this file: python -m unittest tests.test_accounts -v
#              Spec sheet: docs/specs/user-swap.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from flask import session

from url_shortener import app
from app import accounts

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class SessionTestCase(unittest.TestCase):
    """Base class: opens a fake request so session works like it does live."""

    def setUp(self):
        """Pushes a test request context."""
        app.config["TESTING"] = True
        context = app.test_request_context("/")
        context.push()
        self.addCleanup(context.pop)


class TestAddAccount(SessionTestCase):
    """Checks accounts get remembered after logging in."""

    def test_first_login_is_active(self):
        """The first account becomes the active one."""
        accounts.add_account(1)
        self.assertEqual(accounts.current_user_id(), 1)
        self.assertEqual(accounts.signed_in_ids(), [1])

    def test_newest_login_goes_first(self):
        """A second login is active and listed first."""
        accounts.add_account(1)
        accounts.add_account(2)
        self.assertEqual(accounts.current_user_id(), 2)
        self.assertEqual(accounts.signed_in_ids(), [2, 1])

    def test_same_account_twice_not_duplicated(self):
        """Logging in again just moves that account to the front."""
        for user_id in (1, 2, 1):
            accounts.add_account(user_id)
        self.assertEqual(accounts.signed_in_ids(), [1, 2])

    def test_list_capped_at_max(self):
        """Only MAX_ACCOUNTS are kept, the oldest falls off."""
        for user_id in range(1, accounts.MAX_ACCOUNTS + 2):
            accounts.add_account(user_id)
        self.assertEqual(len(accounts.signed_in_ids()), accounts.MAX_ACCOUNTS)
        self.assertNotIn(1, accounts.signed_in_ids())


class TestSwitchTo(SessionTestCase):
    """Checks swapping between signed in accounts."""

    def test_switch_to_signed_in_account(self):
        """Swapping to an account that logged in here works."""
        accounts.add_account(1)
        accounts.add_account(2)
        self.assertTrue(accounts.switch_to(1))
        self.assertEqual(accounts.current_user_id(), 1)

    def test_switch_to_stranger_refused(self):
        """An account that never logged in here can't be swapped to."""
        accounts.add_account(1)
        self.assertFalse(accounts.switch_to(99))
        self.assertEqual(accounts.current_user_id(), 1)  # Nothing Changed


class TestRemoveActiveAccount(SessionTestCase):
    """Checks logging out one account at a time."""

    def test_next_account_takes_over(self):
        """Logging out the active one makes the next most recent active."""
        accounts.add_account(1)
        accounts.add_account(2)
        self.assertEqual(accounts.remove_active_account(), 1)
        self.assertEqual(accounts.signed_in_ids(), [1])

    def test_last_account_leaves_nobody(self):
        """Logging out the only account leaves nobody signed in."""
        accounts.add_account(1)
        self.assertIsNone(accounts.remove_active_account())
        self.assertIsNone(accounts.current_user_id())
        self.assertNotIn(accounts.ACTIVE_KEY, session)


class TestSwitchChoices(SessionTestCase):
    """Checks the list the header menu shows."""

    @mock.patch("app.accounts.get_user_by_id")
    def test_marks_active_and_skips_deleted(self, get_user_by_id):
        """The active account is flagged and deleted accounts are left out."""
        names = {1: {"username": "dan"}, 2: None, 3: {"username": "sam"}}
        get_user_by_id.side_effect = names.get
        for user_id in (1, 2, 3):
            accounts.add_account(user_id)
        choices = accounts.switch_choices()
        self.assertEqual([c["username"] for c in choices], ["sam", "dan"])
        self.assertTrue(choices[0]["active"])
        self.assertFalse(choices[1]["active"])


class TestSwitchRoute(unittest.TestCase):
    """Checks POST /switch/<user_id> through Flask's test client."""

    def setUp(self):
        """Makes a test client with two accounts already signed in."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess[accounts.ACCOUNTS_KEY] = [2, 1]
            sess[accounts.ACTIVE_KEY] = 2

    def test_switch_redirects_and_changes_active(self):
        """Swapping to account 1 redirects to / and makes 1 active."""
        response = self.client.post("/switch/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess[accounts.ACTIVE_KEY], 1)

    def test_switch_to_stranger_is_403(self):
        """An account not signed in here gives 403."""
        self.assertEqual(self.client.post("/switch/99").status_code, 403)

    def test_get_not_allowed(self):
        """A plain link (GET) can't swap accounts."""
        self.assertEqual(self.client.get("/switch/1").status_code, 405)


if __name__ == "__main__":
    unittest.main()
