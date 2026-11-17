# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: tests/test_routes.py
# Version: V1.3
# Description: Unit tests for app/routes.py using Flask's test client.
#
#              Uses Flask's test client against the home page and checks
#              unknown pages 404 (with the short link lookup mocked). The
#              users table is mocked (list_users) so no MySQL is needed.
#              Run just this file: python -m unittest tests.test_routes -v
#              Spec sheet: docs/specs/home-page.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from url_shortener import app

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestRoutes(unittest.TestCase):
    """Checks the app loads through url_shortener:app and serves its pages."""

    def setUp(self):
        """Makes a test client and fakes an empty users table."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        patcher = mock.patch("app.accounts.list_users", return_value=[])  # The Picker's Dropdown Reads This
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_home_page_loads(self):
        """GET / returns 200 and the page title."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"URL Shortener", response.data)

    def test_index_page_loads(self):
        """GET /index serves the same page."""
        self.assertEqual(self.client.get("/index").status_code, 200)

    @mock.patch("app.redirect.get_url_by_code", return_value=None)
    def test_unknown_page_is_404(self, get_url_by_code):
        """A page that doesn't exist (and isn't a short code) returns 404."""
        self.assertEqual(self.client.get("/no-such-page").status_code, 404)


if __name__ == "__main__":
    unittest.main()
