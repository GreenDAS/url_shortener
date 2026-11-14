# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: tests/test_picker.py
# Version: V1.1
# Description: Unit tests for the user picker (URL-13): the header in
#              app/templates/base.html, POST /users in app/routes.py and
#              POST /switch in app/accounts.py.
#
#              Uses Flask's test client, which keeps the session cookie
#              between requests like a browser does. The users table is
#              mocked (list_users, get_user_by_id, create_user) so no MySQL
#              server is needed.
#              Run just this file: python -m unittest tests.test_picker -v
#              Spec sheet: docs/specs/user-picker.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from url_shortener import app
from app import accounts
from app.users import UserError

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
# The Fake users Table, In list_users()'s A To Z Order
USERS = [{"id": 2, "username": "amy"}, {"id": 1, "username": "dan"}]
BY_ID = {user["id"]: user for user in USERS}  # id -> Row, For The Fake get_user_by_id

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class PickerTestCase(unittest.TestCase):
    """Base class: a test client plus a fake users table with amy and dan."""

    def setUp(self):
        """Makes the client and swaps every users table function for a fake."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.list_users = self.patch("app.accounts.list_users", return_value=USERS)
        self.patch("app.accounts.get_user_by_id", side_effect=BY_ID.get)  # switch_to() Uses This One
        self.patch("app.routes.get_user_by_id", side_effect=BY_ID.get)  # current_user() Uses This One
        self.create_user = self.patch("app.routes.create_user", return_value=3)
        self.patch("app.routes.list_urls_for_user", return_value=[])  # The Page Lists Links Too (URL-15)

    def patch(self, target, **kwargs):
        """Starts a mock.patch and stops it when the test ends."""
        patcher = mock.patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def use(self, user_id):
        """Puts a user in the session, as if they were picked earlier."""
        with self.client.session_transaction() as sess:
            sess[accounts.ACTIVE_KEY] = user_id

    def current(self):
        """Reads the current user's id back out of the session."""
        with self.client.session_transaction() as sess:
            return sess.get(accounts.ACTIVE_KEY)


class TestHeader(PickerTestCase):
    """Checks what the header and the page show for each situation."""

    def test_nobody_picked_shows_welcome(self):
        """With no current user the page asks to pick or add one."""
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Pick a user", page)
        self.assertNotIn("Current user:", page)

    def test_dropdown_lists_every_user(self):
        """Each user is an option whose value is its id."""
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('<option value="2" >amy</option>', page)
        self.assertIn('<option value="1" >dan</option>', page)

    def test_current_user_is_selected_and_named(self):
        """The current user is the selected option and is named in the header."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('<option value="1" selected>dan</option>', page)
        self.assertIn("Current user: <strong>dan</strong>", page)

    def test_no_users_means_no_dropdown(self):
        """An empty users table shows only the Add user box."""
        self.list_users.return_value = []
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("<select", page)
        self.assertIn('action="/users"', page)

    def test_deleted_user_in_session_is_treated_as_nobody(self):
        """A session pointing at a user that no longer exists asks to pick again."""
        self.use(99)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("Pick a user", page)

    def test_username_is_escaped(self):
        """A username can't inject HTML into the page."""
        self.list_users.return_value = [{"id": 5, "username": "<b>x</b>"}]
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("<b>x</b>", page)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", page)


class TestAddUser(PickerTestCase):
    """Checks POST /users, the Add user box."""

    def test_add_user_creates_switches_and_redirects(self):
        """A good name is created, becomes the current user and goes back to /."""
        BY_ID[3] = {"id": 3, "username": "zed"}  # The Row create_user "Made"
        self.addCleanup(BY_ID.pop, 3)
        response = self.client.post("/users", data={"username": "zed"})
        self.create_user.assert_called_once_with("zed")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        self.assertEqual(self.current(), 3)

    def test_spaces_around_the_name_are_trimmed(self):
        """ "  zed  " is saved as "zed"."""
        self.client.post("/users", data={"username": "  zed  "})
        self.create_user.assert_called_once_with("zed")

    def test_bad_name_shows_error_and_keeps_the_text(self):
        """A UserError comes back as 400 with the message and the typed name."""
        self.create_user.side_effect = UserError("Username must be 3-50 letters, numbers, '_' or '-'.")
        response = self.client.post("/users", data={"username": "a!"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Username must be 3-50 letters", page)
        self.assertIn('value="a!"', page)

    def test_taken_name_does_not_switch_users(self):
        """A taken name shows the error and the current user stays the same."""
        self.use(1)
        self.create_user.side_effect = UserError("Username 'amy' is already taken.")
        response = self.client.post("/users", data={"username": "amy"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("already taken", response.get_data(as_text=True))
        self.assertEqual(self.current(), 1)

    def test_missing_field_is_sent_to_create_user_as_empty(self):
        """A post with no username field is treated as an empty name."""
        self.create_user.side_effect = UserError("bad")
        self.assertEqual(self.client.post("/users").status_code, 400)
        self.create_user.assert_called_once_with("")

    def test_get_is_not_the_add_route(self):
        """GET /users is not the add route, it falls through to the short link lookup."""
        with mock.patch("app.redirect.get_url_by_code", return_value=None):
            self.assertEqual(self.client.get("/users").status_code, 404)
        self.create_user.assert_not_called()


class TestSwitchForm(PickerTestCase):
    """Checks POST /switch, where the dropdown's form posts."""

    def test_switch_to_picked_user(self):
        """Posting an existing id makes it current and goes back to /."""
        response = self.client.post("/switch", data={"user_id": "2"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        self.assertEqual(self.current(), 2)

    def test_unknown_id_is_404_and_changes_nothing(self):
        """An id with no user gives 404 and the current user stays."""
        self.use(1)
        self.assertEqual(self.client.post("/switch", data={"user_id": "99"}).status_code, 404)
        self.assertEqual(self.current(), 1)

    def test_missing_id_is_404(self):
        """A post with no user_id field gives 404."""
        self.assertEqual(self.client.post("/switch").status_code, 404)

    def test_id_that_is_not_a_number_is_404(self):
        """user_id=abc gives 404 instead of crashing."""
        self.assertEqual(self.client.post("/switch", data={"user_id": "abc"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
