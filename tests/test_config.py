# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/15/2026
# File: tests/test_config.py
# Version: V1.3
# Description: Unit tests for app/config.py (.env loading, spec DB-2).
#
#              Uses mock.patch.dict(os.environ) and temporary .env files so each
#              test controls exactly what load_config() sees, and checks that
#              real environment variables beat the .env file.
#              Run just this file: python -m unittest tests.test_config -v
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import os
import tempfile
import unittest
from unittest import mock

from app.config import load_config

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
CONFIG_KEYS = ("MYSQL_HOST", "MYSQL_PORT", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB", "SECRET_KEY", "SITE_URL")

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestLoadConfig(unittest.TestCase):
    """Checks that load_config() reads .env files and the environment correctly."""

    def setUp(self):
        """Starts every test with none of the config variables set."""
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        for key in CONFIG_KEYS:
            os.environ.pop(key, None)  # Clears Anything Left From The Real Shell

    def tearDown(self):
        """Puts the real environment back."""
        self.env.stop()

    def write_env(self, text):
        """
        Writes a temporary .env file.
        Arg1 = text, the file contents
        Returns: path to the file
        """
        handle = tempfile.NamedTemporaryFile("w", suffix=".env", delete=False)
        handle.write(text)
        handle.close()
        self.addCleanup(os.remove, handle.name)
        return handle.name

    def test_defaults_point_at_host_docker_internal(self):
        """With no .env, MySQL defaults to the host laptop's MySQL: host.docker.internal:3306 (DB-1, DB-2)."""
        config = load_config(self.write_env(""))
        self.assertEqual(config["MYSQL_HOST"], "host.docker.internal")
        self.assertEqual(config["MYSQL_PORT"], 3306)

    def test_site_url_defaults_to_url_short_com(self):
        """With no .env, the short links start with http://url.short.com."""
        config = load_config(self.write_env(""))
        self.assertEqual(config["SITE_URL"], "http://url.short.com")

    def test_site_url_can_be_set_in_env_file(self):
        """SITE_URL in the .env file replaces the default."""
        config = load_config(self.write_env("SITE_URL=http://go.example.com\n"))
        self.assertEqual(config["SITE_URL"], "http://go.example.com")

    def test_site_url_drops_a_slash_on_the_end(self):
        """A "/" typed on the end is removed, so the page never writes "//code"."""
        config = load_config(self.write_env("SITE_URL=http://url.short.com/\n"))
        self.assertEqual(config["SITE_URL"], "http://url.short.com")

    def test_reads_values_from_env_file(self):
        """Values in the .env file end up in the config."""
        path = self.write_env(
            "MYSQL_HOST=host.docker.internal\nMYSQL_PORT=3306\nMYSQL_USER=geneva\n"
            "MYSQL_PASSWORD=pw\nMYSQL_DB=csc203_urls\nSECRET_KEY=abc\n"
        )
        config = load_config(path)
        self.assertEqual(config["MYSQL_USER"], "geneva")
        self.assertEqual(config["MYSQL_PASSWORD"], "pw")
        self.assertEqual(config["MYSQL_DB"], "csc203_urls")
        self.assertEqual(config["SECRET_KEY"], "abc")

    def test_port_is_an_int(self):
        """MYSQL_PORT comes back as a number, ready for PyMySQL."""
        config = load_config(self.write_env("MYSQL_PORT=3306\n"))
        self.assertIsInstance(config["MYSQL_PORT"], int)
        self.assertEqual(config["MYSQL_PORT"], 3306)

    def test_real_environment_wins_over_env_file(self):
        """A variable already set in the environment is not overwritten by .env."""
        os.environ["MYSQL_HOST"] = "db"
        config = load_config(self.write_env("MYSQL_HOST=host.docker.internal\n"))
        self.assertEqual(config["MYSQL_HOST"], "db")


if __name__ == "__main__":
    unittest.main()
