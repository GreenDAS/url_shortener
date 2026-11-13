# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_redirect.py
# Version: V1.2
# Description: Unit tests for app/redirect.py using Flask's test client. The
#              database lookups are mocked so no MySQL server is needed.
#
#              Uses Flask's test client so real HTTP requests go through the
#              routing. get_url_by_code is mocked in app.redirect (where it
#              is used, not where it is defined). Click counting is gone
#              (URL-25), so one test checks no trace of it is left.
#              Run just this file: python -m unittest tests.test_redirect -v
#              Spec sheet: docs/specs/redirect.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from url_shortener import app
from app import redirect as redirect_module
from app import urls

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestFollowShortLink(unittest.TestCase):
    """Checks /<code> redirects known codes and 404s unknown ones."""

    def setUp(self):
        """Makes a test client and mocks the urls.py lookup the route uses."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        lookup = mock.patch("app.redirect.get_url_by_code")
        self.get_url_by_code = lookup.start()
        self.addCleanup(lookup.stop)

    def test_known_code_redirects_with_302(self):
        """A saved code sends a 302 to its long URL."""
        self.get_url_by_code.return_value = {"code": "abc123", "long_url": "https://example.com/page"}
        response = self.client.get("/abc123")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "https://example.com/page")

    def test_known_code_runs_only_the_lookup(self):
        """Following a link does one lookup and nothing else (no click UPDATE)."""
        self.get_url_by_code.return_value = {"code": "abc123", "long_url": "https://example.com"}
        self.client.get("/abc123")
        self.get_url_by_code.assert_called_once_with("abc123")

    def test_no_click_counting_code_left(self):
        """record_click() is gone from both urls.py and redirect.py (URL-25)."""
        self.assertFalse(hasattr(urls, "record_click"))
        self.assertFalse(hasattr(redirect_module, "record_click"))

    def test_unknown_code_is_404(self):
        """A code that isn't saved gives 404."""
        self.get_url_by_code.return_value = None
        self.assertEqual(self.client.get("/nope99").status_code, 404)

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
