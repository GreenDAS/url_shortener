# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: tests/test_urls.py
# Version: V1.0
# Description: Unit tests for app/urls.py. get_db() is replaced with a mock
#              so no MySQL server is needed.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

import pymysql

from url_shortener import app
from app import urls

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DUPLICATE = pymysql.err.IntegrityError(1062, "Duplicate entry")  # What MySQL Raises On A UNIQUE Clash

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class UrlsTestCase(unittest.TestCase):
    """Base class: swaps get_db() for a fake connection with a fake cursor."""

    def setUp(self):
        """Patches app.urls.get_db and opens an app context."""
        patcher = mock.patch("app.urls.get_db")
        self.get_db = patcher.start()
        self.addCleanup(patcher.stop)
        self.db = self.get_db.return_value
        self.cursor = self.db.cursor.return_value.__enter__.return_value  # What "with db.cursor() as c" Gives
        context = app.app_context()
        context.push()
        self.addCleanup(context.pop)

    def inserts(self):
        """Returns the (sql, params) of every INSERT the code ran."""
        return [c.args for c in self.cursor.execute.call_args_list if c.args[0].startswith("INSERT")]


class TestValidateLongUrl(unittest.TestCase):
    """Checks which long URLs are allowed."""

    def test_http_and_https_pass(self):
        """Both schemes are fine."""
        urls.validate_long_url("http://example.com")
        urls.validate_long_url("https://example.com/a?b=c")

    def test_missing_scheme_fails(self):
        """example.com without http:// is rejected."""
        with self.assertRaises(urls.UrlError):
            urls.validate_long_url("example.com")

    def test_javascript_scheme_fails(self):
        """Only web links, nothing like javascript: that could run code."""
        with self.assertRaises(urls.UrlError):
            urls.validate_long_url("javascript:alert(1)")

    def test_too_long_fails(self):
        """Anything over MAX_URL_LENGTH is rejected."""
        with self.assertRaises(urls.UrlError):
            urls.validate_long_url("https://a.com/" + "x" * urls.MAX_URL_LENGTH)

    def test_spaces_fail(self):
        """A URL with a space in it is rejected."""
        with self.assertRaises(urls.UrlError):
            urls.validate_long_url("https://a.com/has space")


class TestValidateAlias(unittest.TestCase):
    """Checks which custom aliases are allowed."""

    def test_good_alias_passes(self):
        """Letters, numbers, "_" and "-" are allowed."""
        urls.validate_alias("csc-203_x")

    def test_short_alias_fails(self):
        """Under 3 characters is rejected."""
        with self.assertRaises(urls.UrlError):
            urls.validate_alias("ab")

    def test_slash_fails(self):
        """A "/" would break the /<code> route, so it is rejected."""
        with self.assertRaises(urls.UrlError):
            urls.validate_alias("a/b/c")

    def test_reserved_word_fails_any_case(self):
        """Page names like login are reserved, even typed as LOGIN."""
        for word in ("login", "LOGIN", "Api"):
            with self.subTest(word=word), self.assertRaises(urls.UrlError):
                urls.validate_alias(word)


class TestGenerateCode(unittest.TestCase):
    """Checks the random code maker."""

    def test_length_and_characters(self):
        """Codes are CODE_LENGTH long and only use CODE_ALPHABET."""
        code = urls.generate_code()
        self.assertEqual(len(code), urls.CODE_LENGTH)
        self.assertTrue(set(code) <= set(urls.CODE_ALPHABET))

    def test_codes_differ(self):
        """100 codes in a row are all different."""
        self.assertEqual(len({urls.generate_code() for _ in range(100)}), 100)


class TestCreateUrl(UrlsTestCase):
    """Checks create_url() for random codes, aliases and clashes."""

    def test_random_code_saved_and_committed(self):
        """Without an alias a random code is inserted and committed."""
        with mock.patch("app.urls.generate_code", return_value="abc123"):
            self.cursor.fetchone.return_value = {"code": "abc123"}
            self.assertEqual(urls.create_url(1, "https://a.com")["code"], "abc123")
        self.assertEqual(self.inserts()[0][1], (1, "abc123", "https://a.com"))
        self.db.commit.assert_called_once()

    def test_random_code_clash_retries(self):
        """If the first code is taken a new one is tried."""
        self.cursor.execute.side_effect = [DUPLICATE, None, None]  # Insert Fails, Insert Works, Select
        with mock.patch("app.urls.generate_code", side_effect=["taken1", "free22"]):
            urls.create_url(1, "https://a.com")
        self.assertEqual([params[1] for _, params in self.inserts()], ["taken1", "free22"])
        self.db.rollback.assert_called_once()

    def test_gives_up_after_max_tries(self):
        """Clashing every time ends with UrlError, not a loop forever."""
        self.cursor.execute.side_effect = DUPLICATE
        with self.assertRaises(urls.UrlError):
            urls.create_url(1, "https://a.com")
        self.assertEqual(len(self.inserts()), urls.MAX_CODE_TRIES)

    def test_alias_is_used_as_code(self):
        """A custom alias is saved as the code."""
        urls.create_url(1, "https://a.com", alias="csc203")
        self.assertEqual(self.inserts()[0][1][1], "csc203")

    def test_taken_alias_raises_alias_taken(self):
        """A used alias raises AliasTakenError and does not retry."""
        self.cursor.execute.side_effect = DUPLICATE
        with self.assertRaises(urls.AliasTakenError):
            urls.create_url(1, "https://a.com", alias="csc203")
        self.assertEqual(len(self.inserts()), 1)

    def test_bad_url_never_touches_db(self):
        """Validation fails before any SQL runs."""
        with self.assertRaises(urls.UrlError):
            urls.create_url(1, "not-a-url")
        self.cursor.execute.assert_not_called()


class TestReadAndDelete(UrlsTestCase):
    """Checks lookups, listing, deleting and click counting."""

    def test_get_by_code_uses_placeholder(self):
        """The code is passed as a parameter, not pasted into the SQL."""
        urls.get_url_by_code("abc123")
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("WHERE code = %s", sql)
        self.assertEqual(params, ("abc123",))

    def test_list_is_newest_first(self):
        """The home page list is ordered newest first for that user."""
        self.cursor.fetchall.return_value = ({"code": "b"}, {"code": "a"})
        self.assertEqual([r["code"] for r in urls.list_urls_for_user(1)], ["b", "a"])
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("ORDER BY created_at DESC", sql)
        self.assertEqual(params, (1,))

    def test_delete_own_link(self):
        """Deleting a link you own returns True."""
        self.cursor.rowcount = 1
        self.assertTrue(urls.delete_url(1, "abc123"))
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("AND user_id = %s", sql)  # Owner Check Is In The SQL
        self.assertEqual(params, ("abc123", 1))

    def test_delete_someone_elses_link(self):
        """Nothing deleted (not yours or missing) returns False."""
        self.cursor.rowcount = 0
        self.assertFalse(urls.delete_url(2, "abc123"))

    def test_record_click(self):
        """A visit adds 1 in SQL and reports the link was found."""
        self.cursor.rowcount = 1
        self.assertTrue(urls.record_click("abc123"))
        self.assertIn("clicks = clicks + 1", self.cursor.execute.call_args.args[0])
        self.db.commit.assert_called_once()

    def test_record_click_missing_code(self):
        """An unknown code reports False."""
        self.cursor.rowcount = 0
        self.assertFalse(urls.record_click("nope"))


if __name__ == "__main__":
    unittest.main()
