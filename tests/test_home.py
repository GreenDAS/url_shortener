# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/13/2026
# File: tests/test_home.py
# Version: V1.0
# Description: Unit tests for the home page (URL-15): the table of the
#              current user's links in app/templates/home.html and the
#              Delete button's route, POST /links/<code>/delete, in
#              app/routes.py.
#
#              Uses Flask's test client. The users and urls tables are
#              mocked (list_users, get_user_by_id, list_urls_for_user,
#              delete_url) so no MySQL server is needed.
#              Run just this file: python -m unittest tests.test_home -v
#              Spec sheet: docs/specs/home-page.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import datetime
import unittest
from unittest import mock

from url_shortener import app
from app import accounts

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DAN = {"id": 1, "username": "dan"}  # The Only User In The Fake users Table

# Two Fake Link Rows, In list_urls_for_user()'s Newest First Order
LINKS = [
    {"id": 8, "user_id": 1, "code": "abc123", "long_url": "https://example.com/new",
     "created_at": datetime.datetime(2026, 11, 13, 21, 30)},
    {"id": 7, "user_id": 1, "code": "repo", "long_url": "https://github.com/GreenDAS/url_shortener",
     "created_at": datetime.datetime(2026, 11, 2, 9, 5)},
]

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class HomeTestCase(unittest.TestCase):
    """Base class: a test client, a fake users table with dan, and fake links."""

    def setUp(self):
        """Makes the client and swaps the database functions for fakes."""
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.patch("app.accounts.list_users", return_value=[DAN])
        self.patch("app.routes.get_user_by_id", side_effect={1: DAN}.get)  # Only id 1 Exists
        self.list_urls = self.patch("app.routes.list_urls_for_user", return_value=LINKS)
        self.delete_url = self.patch("app.routes.delete_url", return_value=True)

    def patch(self, target, **kwargs):
        """Starts a mock.patch and stops it when the test ends."""
        patcher = mock.patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def use(self, user_id):
        """Puts a user in the session, as if they were picked earlier."""
        with self.client.session_transaction() as sess:
            sess[accounts.ACTIVE_KEY] = user_id


class TestLinksTable(HomeTestCase):
    """Checks the table of links on GET /."""

    def test_lists_only_the_current_users_links(self):
        """The page asks list_urls_for_user() for the current user's id and nobody else's."""
        self.use(1)
        self.client.get("/")
        self.list_urls.assert_called_once_with(1)

    def test_nobody_picked_does_not_ask_for_links(self):
        """With no current user there is no table and the urls table isn't read."""
        page = self.client.get("/").get_data(as_text=True)
        self.list_urls.assert_not_called()
        self.assertNotIn("<table>", page)

    def test_each_link_is_a_row_with_its_short_link(self):
        """Every link shows the site address + code as a clickable link, and its long URL."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('<a href="http://localhost/abc123">http://localhost/abc123</a>', page)
        self.assertIn('<a href="http://localhost/repo">http://localhost/repo</a>', page)
        self.assertIn("https://github.com/GreenDAS/url_shortener", page)

    def test_short_link_uses_the_address_the_browser_used(self):
        """Opened as url.short.com, the short links say url.short.com."""
        with self.client.session_transaction(base_url="http://url.short.com") as sess:
            sess[accounts.ACTIVE_KEY] = 1  # The Cookie Belongs To The Domain It Was Set On
        page = self.client.get("/", base_url="http://url.short.com").get_data(as_text=True)
        self.assertIn("http://url.short.com/abc123", page)

    def test_rows_keep_newest_first_order(self):
        """The rows are in the order list_urls_for_user() returned (newest first)."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertLess(page.index("abc123"), page.index("/repo"))

    def test_created_date_is_month_day_year(self):
        """created_at is shown as MM/DD/YYYY."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("<td>11/13/2026</td>", page)
        self.assertIn("<td>11/02/2026</td>", page)

    def test_each_row_has_a_delete_form(self):
        """Every row has a POST form aimed at its own code."""
        self.use(1)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn('<form method="post" action="/links/abc123/delete">', page)
        self.assertIn('<form method="post" action="/links/repo/delete">', page)

    def test_user_with_no_links_sees_a_message(self):
        """An empty list shows "No links yet." and no table."""
        self.use(1)
        self.list_urls.return_value = []
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("No links yet.", page)
        self.assertNotIn("<table>", page)

    def test_long_url_is_escaped(self):
        """A long URL with HTML in it is shown as text, not run."""
        self.use(1)
        self.list_urls.return_value = [dict(LINKS[0], long_url="https://example.com/?q=<script>x</script>")]
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("<script>x</script>", page)
        self.assertIn("&lt;script&gt;", page)


class TestDeleteLink(HomeTestCase):
    """Checks POST /links/<code>/delete, the Delete button."""

    def test_delete_my_link_redirects_home(self):
        """Deleting passes my id and the code to delete_url() and goes back to /."""
        self.use(1)
        response = self.client.post("/links/repo/delete")
        self.delete_url.assert_called_once_with(1, "repo")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_delete_someone_elses_link_is_404(self):
        """delete_url() returning False (not mine, or no such link) gives 404."""
        self.use(1)
        self.delete_url.return_value = False
        self.assertEqual(self.client.post("/links/amys/delete").status_code, 404)

    def test_delete_with_nobody_picked_deletes_nothing(self):
        """With no current user it goes back to / and never calls delete_url()."""
        response = self.client.post("/links/repo/delete")
        self.assertEqual(response.status_code, 302)
        self.delete_url.assert_not_called()

    def test_delete_must_be_a_post(self):
        """Opening the address with GET is refused (405) and deletes nothing."""
        self.use(1)
        self.assertEqual(self.client.get("/links/repo/delete").status_code, 405)
        self.delete_url.assert_not_called()

    def test_code_is_passed_as_typed(self):
        """The code keeps its upper and lower case on the way to delete_url()."""
        self.use(1)
        self.client.post("/links/AbC_1-2/delete")
        self.delete_url.assert_called_once_with(1, "AbC_1-2")


if __name__ == "__main__":
    unittest.main()
