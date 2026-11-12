# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_accounts.py
# Version: V1.2
# Description: Unit tests for app/accounts.py (URL-12 user swapping). Uses a
#              test request so there is a real session, and mocks the users
#              table so no MySQL server is needed.
#
#              Runs each test inside app.test_request_context() so the session
#              works without a browser. get_user_by_id and list_users are
#              mocked so no MySQL is needed. Covers switching to a real or
#              unknown user, the choices list and the POST /switch/<id>
#              route (redirect, 404 and 405).
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


class TestSwitchTo(SessionTestCase):
    """Checks swapping the current user (URL-24)."""

    def test_nobody_is_current_at_first(self):
        """A fresh session has no current user."""
        self.assertIsNone(accounts.current_user_id())

    @mock.patch("app.accounts.get_user_by_id", return_value={"id": 1, "username": "dan"})
    def test_switch_to_existing_user(self, get_user_by_id):
        """Any user that exists can be switched to, no sign in needed."""
        self.assertTrue(accounts.switch_to(1))
        self.assertEqual(accounts.current_user_id(), 1)
        self.assertEqual(session[accounts.ACTIVE_KEY], 1)

    @mock.patch("app.accounts.get_user_by_id")
    def test_switch_again_replaces_current_user(self, get_user_by_id):
        """A second switch replaces the first, only one user is current."""
        get_user_by_id.side_effect = lambda user_id: {"id": user_id, "username": f"user{user_id}"}
        accounts.switch_to(1)
        accounts.switch_to(2)
        self.assertEqual(accounts.current_user_id(), 2)

    @mock.patch("app.accounts.get_user_by_id")
    def test_switch_to_unknown_user_changes_nothing(self, get_user_by_id):
        """An id with no user is refused and the current user stays."""
        get_user_by_id.return_value = {"id": 1, "username": "dan"}
        accounts.switch_to(1)
        get_user_by_id.return_value = None  # User 99 Does Not Exist
        self.assertFalse(accounts.switch_to(99))
        self.assertEqual(accounts.current_user_id(), 1)  # Nothing Changed


class TestSwitchChoices(SessionTestCase):
    """Checks the list the "Switch user" control shows."""

    @mock.patch("app.accounts.list_users")
    def test_lists_every_user_and_marks_current(self, list_users):
        """Every user is listed in list_users() order and only the current one is active."""
        list_users.return_value = [{"id": 2, "username": "amy"}, {"id": 1, "username": "dan"}]
        session[accounts.ACTIVE_KEY] = 1
        choices = accounts.switch_choices()
        self.assertEqual([c["username"] for c in choices], ["amy", "dan"])
        self.assertEqual([c["active"] for c in choices], [False, True])
        self.assertEqual([c["id"] for c in choices], [2, 1])

    @mock.patch("app.accounts.list_users")
    def test_nobody_active_before_first_switch(self, list_users):
        """With no current user, no choice is marked active."""
        list_users.return_value = [{"id": 1, "username": "dan"}]
        self.assertFalse(accounts.switch_choices()[0]["active"])

    @mock.patch("app.accounts.list_users", return_value=[])
    def test_no_users_gives_empty_list(self, list_users):
        """An empty users table gives an empty list."""
        self.assertEqual(accounts.switch_choices(), [])


class TestSwitchRoute(unittest.TestCase):
    """Checks POST /switch/<user_id> through Flask's test client."""

    def setUp(self):
        """Makes a test client where user 2 is current, and fakes the users table."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess[accounts.ACTIVE_KEY] = 2
        patcher = mock.patch("app.accounts.get_user_by_id")
        self.get_user_by_id = patcher.start()
        self.addCleanup(patcher.stop)
        known = {1: {"id": 1, "username": "dan"}, 2: {"id": 2, "username": "amy"}}
        self.get_user_by_id.side_effect = known.get  # Only Users 1 And 2 Exist

    def test_switch_redirects_and_changes_current_user(self):
        """Swapping to user 1 redirects to / and makes 1 current."""
        response = self.client.post("/switch/1")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as sess:
            self.assertEqual(sess[accounts.ACTIVE_KEY], 1)

    def test_switch_to_unknown_user_is_404(self):
        """An id with no user gives 404 and the current user stays."""
        self.assertEqual(self.client.post("/switch/99").status_code, 404)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess[accounts.ACTIVE_KEY], 2)

    def test_non_number_id_is_not_a_switch(self):
        """POST /switch/abc never reaches switch_user(), so it can't change the user."""
        self.assertIn(self.client.post("/switch/abc").status_code, (404, 405))
        self.get_user_by_id.assert_not_called()

    def test_get_not_allowed(self):
        """A plain link (GET) can't swap users."""
        self.assertEqual(self.client.get("/switch/1").status_code, 405)


if __name__ == "__main__":
    unittest.main()
