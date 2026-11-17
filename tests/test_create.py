# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: tests/test_create.py
# Version: V1.0
# Description: Unit tests for the create short link form (URL-14) and its
#              custom alias box (URL-22): the form in
#              app/templates/home.html and POST /links in app/routes.py.
#
#              Uses Flask's test client. create_url() is mocked, so these
#              tests check what the route passes to it and what the page
#              shows for each outcome. The alias and URL rules themselves
#              are tested in tests/test_urls.py. No MySQL server is needed.
#              Run just this file: python -m unittest tests.test_create -v
#              Spec sheet: docs/specs/create-form.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from url_shortener import app
from app import accounts
from app.urls import AliasTakenError, UrlError

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DAN = {"id": 1, "username": "dan"}  # The Only User In The Fake users Table
LONG_URL = "https://example.com/a/long/address"

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class CreateTestCase(unittest.TestCase):
    """Base class: a test client, a fake users table with dan, and a fake create_url()."""

    def setUp(self):
        """Makes the client and swaps the database functions for fakes."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.patch("app.accounts.list_users", return_value=[DAN])
        self.patch("app.routes.get_user_by_id", side_effect={1: DAN}.get)  # Only id 1 Exists
        self.patch("app.routes.list_urls_for_user", return_value=[])
        self.create_url = self.patch("app.routes.create_url")

    def patch(self, target, **kwargs):
        """Starts a mock.patch and stops it when the test ends."""
        patcher = mock.patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def use(self, user_id):
        """Puts a user in the session, as if they were picked earlier."""
        with self.client.session_transaction() as sess:
            sess[accounts.ACTIVE_KEY] = user_id


class TestCreateForm(CreateTestCase):
    """Checks the form itself on GET /."""

    def test_form_shows_for_the_current_user(self):
        """With a user picked the page has the form with both boxes."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('<form method="post" action="/links">', page)
        self.assertIn('name="long_url"', page)
        self.assertIn('name="alias"', page)

    def test_form_is_hidden_when_nobody_is_picked(self):
        """A link needs an owner, so with no current user there is no form."""
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn('action="/links"', page)


class TestCreateLink(CreateTestCase):
    """Checks POST /links."""

    def test_empty_alias_asks_for_a_random_code(self):
        """An empty alias box reaches create_url() as None, which means random."""
        self.use(1)
        response = self.client.post("/links", data={"long_url": LONG_URL, "alias": ""})
        self.create_url.assert_called_once_with(1, LONG_URL, None)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_missing_alias_field_also_means_random(self):
        """A post with no alias field at all is the same as an empty box."""
        self.use(1)
        self.client.post("/links", data={"long_url": LONG_URL})
        self.create_url.assert_called_once_with(1, LONG_URL, None)

    def test_alias_is_passed_through(self):
        """A typed alias reaches create_url() and the page goes back to /."""
        self.use(1)
        response = self.client.post("/links", data={"long_url": LONG_URL, "alias": "csc203"})
        self.create_url.assert_called_once_with(1, LONG_URL, "csc203")
        self.assertEqual(response.status_code, 302)

    def test_alias_keeps_its_case(self):
        """CSC203 is not lowercased, aliases are case sensitive (URL-22)."""
        self.use(1)
        self.client.post("/links", data={"long_url": LONG_URL, "alias": "CSC203"})
        self.create_url.assert_called_once_with(1, LONG_URL, "CSC203")

    def test_spaces_around_both_fields_are_trimmed(self):
        """Spaces before and after the URL and the alias are dropped."""
        self.use(1)
        self.client.post("/links", data={"long_url": f"  {LONG_URL} ", "alias": " csc203  "})
        self.create_url.assert_called_once_with(1, LONG_URL, "csc203")

    def test_link_is_owned_by_the_current_user(self):
        """The first argument to create_url() is the id from the session."""
        self.use(1)
        self.client.post("/links", data={"long_url": LONG_URL})
        self.assertEqual(self.create_url.call_args.args[0], 1)

    def test_bad_url_shows_error_above_form_and_keeps_text(self):
        """A UrlError comes back as 400 with the message and what was typed."""
        self.use(1)
        self.create_url.side_effect = UrlError("URL must start with http:// or https://")
        response = self.client.post("/links", data={"long_url": "ftp://x", "alias": "mine"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("URL must start with http:// or https://", page)
        self.assertIn('value="ftp://x"', page)
        self.assertIn('value="mine"', page)
        self.assertLess(page.index('class="error"'), page.index('action="/links"'))  # Error Is Above The Form

    def test_taken_alias_shows_error(self):
        """AliasTakenError is a UrlError too, so it is shown the same way."""
        self.use(1)
        self.create_url.side_effect = AliasTakenError("'csc203' is already taken.")
        response = self.client.post("/links", data={"long_url": LONG_URL, "alias": "csc203"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("is already taken.", response.get_data(as_text=True))

    def test_reserved_alias_shows_error(self):
        """A reserved word comes back from create_url() as a UrlError and is shown."""
        self.use(1)
        self.create_url.side_effect = UrlError("'login' is reserved by the site.")
        response = self.client.post("/links", data={"long_url": LONG_URL, "alias": "login"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("is reserved by the site.", response.get_data(as_text=True))

    def test_nobody_picked_creates_nothing(self):
        """With no current user it goes back to / and never calls create_url()."""
        response = self.client.post("/links", data={"long_url": LONG_URL})
        self.assertEqual(response.status_code, 302)
        self.create_url.assert_not_called()

    def test_get_is_not_the_create_route(self):
        """GET /links is not the create route, it falls through to the short link lookup."""
        self.use(1)
        with mock.patch("app.redirect.get_url_by_code", return_value=None):
            self.assertEqual(self.client.get("/links").status_code, 404)
        self.create_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
