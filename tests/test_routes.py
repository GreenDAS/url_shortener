# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: tests/test_routes.py
# Version: V1.0
# Description: Unit tests for app/routes.py using Flask's test client.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest

from url_shortener import app

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestRoutes(unittest.TestCase):
    """Checks the app loads through url_shortener:app and serves its pages."""

    def setUp(self):
        """Makes a test client so no server is needed."""
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_page_loads(self):
        """GET / returns 200 and the placeholder text."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hello, World!", response.data)

    def test_index_page_loads(self):
        """GET /index serves the same page."""
        self.assertEqual(self.client.get("/index").status_code, 200)

    def test_unknown_page_is_404(self):
        """A page that doesn't exist returns 404."""
        self.assertEqual(self.client.get("/no-such-page").status_code, 404)


if __name__ == "__main__":
    unittest.main()
