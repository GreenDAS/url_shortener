# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_compose.py
# Version: V1.0
# Description: Unit tests that keep MySQL out of Docker (URL-29, spec DB-1).
#              Reads compose.yaml and .env.example as plain text, with the
#              comments stripped, and checks there is no db service, volume
#              or root password left and that the app still points at the
#              host's MySQL. No Docker, YAML package or MySQL is needed.
#              Run just this file: python -m unittest tests.test_compose -v
#              Spec sheet: docs/specs/host-mysql.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import unittest
from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent  # tests/ -> Repo Folder

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def settings_lines(name):
    """
    Reads a config file and drops its comments, so a word that only appears
    in a comment (like "MySQL is NOT in here") can't fail or pass a test.
    Arg1 = name, file name in the repo folder (e.g. "compose.yaml")
    Returns: list of the file's lines with "#" comments and blank lines removed
    """
    lines = []
    for line in (REPO / name).read_text(encoding="utf-8").splitlines():
        code = line.split("#", 1)[0].rstrip()  # Cut Everything After "#"
        if code.strip():  # Skip Lines That Were Only A Comment Or Blank
            lines.append(code)
    return lines

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestComposeHasNoDatabase(unittest.TestCase):
    """Checks compose.yaml only runs the app container."""

    def setUp(self):
        """Loads compose.yaml without its comments."""
        self.lines = settings_lines("compose.yaml")
        self.text = "\n".join(self.lines)

    def test_only_the_web_service(self):
        """The services block has web and nothing else (no db service)."""
        services = [line.strip() for line in self.lines if line.startswith("  ") and not line.startswith("   ")]
        self.assertEqual(services, ["web:"])

    def test_no_mysql_image_or_volume(self):
        """No MySQL image, data volume or wait-for-db is left."""
        for word in ("mysql", "volumes", "db_data", "depends_on", "MYSQL_ROOT_PASSWORD"):
            self.assertNotIn(word, self.text)

    def test_container_can_still_reach_the_host(self):
        """host.docker.internal is still mapped to the host (DOC-5), which is how MySQL is reached."""
        self.assertIn('"host.docker.internal:host-gateway"', self.text)

    def test_app_port_still_published(self):
        """Port 5000 is still published for Gunicorn (DOC-4)."""
        self.assertIn('"5000:5000"', self.text)


class TestEnvExample(unittest.TestCase):
    """Checks .env.example points at the host's MySQL."""

    def setUp(self):
        """Loads .env.example without its comments into a dict."""
        self.values = dict(line.split("=", 1) for line in settings_lines(".env.example"))

    def test_host_and_port_are_the_laptop_mysql(self):
        """MYSQL_HOST is host.docker.internal (DB-2) and the port is the host's 3306."""
        self.assertEqual(self.values["MYSQL_HOST"], "host.docker.internal")
        self.assertEqual(self.values["MYSQL_PORT"], "3306")

    def test_no_root_password(self):
        """The app never needs MySQL's root password now that Compose doesn't create MySQL."""
        self.assertNotIn("MYSQL_ROOT_PASSWORD", self.values)

    def test_app_user_settings_present(self):
        """The dedicated app user, its password and the database name are still there (DB-3)."""
        for key in ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DB", "SECRET_KEY"):
            self.assertIn(key, self.values)


if __name__ == "__main__":
    unittest.main()
