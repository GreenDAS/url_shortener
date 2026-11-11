# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_redirect.py
# Version: V1.1
# Description: Unit tests for app/redirect.py using Flask's test client. The
#              database lookups are mocked so no MySQL server is needed.
#
#              Uses Flask's test client so real HTTP requests go through the
#              routing. get_url_by_code and record_click are mocked in
#              app.redirect (where they are used, not where they are defined).
#              Run just this file: python -m unittest tests.test_redirect -v
#              Spec sheet: docs/specs/redirect.md
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
class TestFollowShortLink(unittest.TestCase):
    """Checks /<code> redirects known codes and 404s unknown ones."""

    def setUp(self):
        """Makes a test client and mocks the two urls.py functions the route uses."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        lookup = mock.patch("app.redirect.get_url_by_code")
        click = mock.patch("app.redirect.record_click")
        self.get_url_by_code = lookup.start()
        self.record_click = click.start()
        self.addCleanup(lookup.stop)
        self.addCleanup(click.stop)

    def test_known_code_redirects_with_302(self):
        """A saved code sends a 302 to its long URL."""
        self.get_url_by_code.return_value = {"code": "abc123", "long_url": "https://example.com/page"}
        response = self.client.get("/abc123")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "https://example.com/page")

    def test_known_code_counts_click(self):
        """Following a link records one click for that code."""
        self.get_url_by_code.return_value = {"code": "abc123", "long_url": "https://example.com"}
        self.client.get("/abc123")
        self.record_click.assert_called_once_with("abc123")

    def test_unknown_code_is_404(self):
        """A code that isn't saved gives 404 and counts nothing."""
        self.get_url_by_code.return_value = None
        self.assertEqual(self.client.get("/nope99").status_code, 404)
        self.record_click.assert_not_called()

    def test_fixed_routes_win_over_codes(self):
        """/index is a real page, so it never reaches the short link lookup."""
        self.assertEqual(self.client.get("/index").status_code, 200)
        self.get_url_by_code.assert_not_called()

    def test_codes_are_case_sensitive(self):
        """/ABC123 is looked up as typed, not lowercased."""
        self.get_url_by_code.return_value = None
        self.client.get("/ABC123")
        self.get_url_by_code.assert_called_once_with("ABC123")


if __name__ == "__main__":
    unittest.main()
