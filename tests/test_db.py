# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_db.py
# Version: V1.1
# Description: Unit tests for app/db.py. MySQL is faked with unittest.mock so
#              these run without a database server.
#
#              pymysql.connect is mocked, so tests check the settings passed to
#              it, that one connection is reused per request and closed at
#              teardown, how schema.sql is split, and the init-db command.
#              Run just this file: python -m unittest tests.test_db -v
#              Spec sheet: docs/specs/database.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from unittest import mock

from url_shortener import app
from app import db

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestSplitSqlStatements(unittest.TestCase):
    """Checks .sql text gets broken into single statements correctly."""

    def test_splits_on_semicolons(self):
        """Two statements come back as two list items."""
        self.assertEqual(db.split_sql_statements("SELECT 1; SELECT 2;"), ["SELECT 1", "SELECT 2"])

    def test_drops_comments_and_blank_lines(self):
        """Full line and end of line "--" comments are removed."""
        script = "-- header\n\nSELECT 1 -- trailing\n;\n"
        self.assertEqual(db.split_sql_statements(script), ["SELECT 1"])

    def test_schema_has_users_table(self):
        """The real schema.sql contains the users table statement."""
        with open("app/schema.sql", encoding="utf-8") as f:
            statements = db.split_sql_statements(f.read())
        self.assertTrue(any("CREATE TABLE IF NOT EXISTS users" in s for s in statements))


class TestConnection(unittest.TestCase):
    """Checks get_db() and close_db() open and close one connection per request."""

    def setUp(self):
        """Saves the MySQL config so each test can change it."""
        self.saved = {k: app.config.get(k) for k in ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER")}

    def tearDown(self):
        """Puts the MySQL config back."""
        for key, value in self.saved.items():
            if value is None:
                app.config.pop(key, None)
            else:
                app.config[key] = value

    def test_settings_come_from_app_config(self):
        """Values in app.config win over the defaults."""
        app.config.update(MYSQL_HOST="db.example", MYSQL_PORT="3399", MYSQL_USER="tester")
        with app.app_context():
            settings = db.connection_settings()
        self.assertEqual(settings["host"], "db.example")
        self.assertEqual(settings["port"], 3399)  # Converted To An int
        self.assertEqual(settings["user"], "tester")

    def test_settings_fall_back_to_defaults(self):
        """With nothing set, the laptop defaults are used."""
        for key in self.saved:
            app.config.pop(key, None)
        with mock.patch.dict("os.environ", {}, clear=True), app.app_context():
            settings = db.connection_settings()
        self.assertEqual(settings["host"], db.DEFAULT_MYSQL_HOST)
        self.assertEqual(settings["port"], db.DEFAULT_MYSQL_PORT)

    @mock.patch("app.db.pymysql.connect")
    def test_get_db_reuses_one_connection(self, connect):
        """Calling get_db() twice in a request only connects once."""
        with app.app_context():
            first = db.get_db()
            second = db.get_db()
        self.assertIs(first, second)
        connect.assert_called_once()

    @mock.patch("app.db.pymysql.connect")
    def test_connection_closed_at_teardown(self, connect):
        """The connection is closed when the app context ends."""
        with app.app_context():
            db.get_db()
        connect.return_value.close.assert_called_once()


class TestInitDb(unittest.TestCase):
    """Checks init_db() and the "flask init-db" command run the schema."""

    @mock.patch("app.db.get_db")
    def test_init_db_runs_every_statement_and_commits(self, get_db):
        """Each schema statement is executed, then committed once."""
        cursor = get_db.return_value.cursor.return_value.__enter__.return_value
        with app.app_context():
            count = db.init_db()
        self.assertEqual(cursor.execute.call_count, count)
        get_db.return_value.commit.assert_called_once()

    @mock.patch("app.db.init_db", return_value=1)
    def test_init_db_command(self, init_db):
        """"flask init-db" calls init_db() and prints a message."""
        result = app.test_cli_runner().invoke(args=["init-db"])
        init_db.assert_called_once()
        self.assertIn("Initialized the database", result.output)


if __name__ == "__main__":
    unittest.main()
