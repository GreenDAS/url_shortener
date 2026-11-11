# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: tests/test_gunicorn_config.py
# Version: V1.0
# Description: Unit tests for gunicorn_config.py (spec WSGI-1..4, DOC-3, DOC-6).
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import importlib
import os
import pathlib
import unittest
from unittest import mock

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def load_gunicorn_config(env=None):
    """
    Imports a fresh copy of gunicorn_config.py.
    Arg1 = env, dict of environment variables to set while importing
    Returns: the gunicorn_config module
    """
    with mock.patch.dict(os.environ, env or {}):
        import gunicorn_config
        return importlib.reload(gunicorn_config)

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestGunicornConfig(unittest.TestCase):
    """Checks the Gunicorn settings the spec asks for."""

    def setUp(self):
        """Makes sure APP_PORT from the shell doesn't change the defaults."""
        patcher = mock.patch.dict(os.environ, {})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("APP_PORT", None)

    def test_binds_to_all_addresses_on_5000(self):
        """Gunicorn binds to 0.0.0.0 on port 5000 by default (WSGI-3, WSGI-4)."""
        self.assertEqual(load_gunicorn_config().bind, "0.0.0.0:5000")

    def test_port_can_be_changed(self):
        """APP_PORT picks a different port."""
        self.assertEqual(load_gunicorn_config({"APP_PORT": "8000"}).bind, "0.0.0.0:8000")

    def test_loads_the_right_module_and_app(self):
        """wsgi_app is module:variable of the Flask app (WSGI-2)."""
        self.assertEqual(load_gunicorn_config().wsgi_app, "url_shortener:app")

    def test_logs_go_to_stdout_and_stderr(self):
        """Access and error logs go to the console so docker logs shows them (DOC-6)."""
        config = load_gunicorn_config()
        self.assertEqual(config.accesslog, "-")
        self.assertEqual(config.errorlog, "-")

    def test_has_at_least_one_worker(self):
        """Worker count is a positive number."""
        self.assertGreaterEqual(load_gunicorn_config().workers, 1)

    def test_gunicorn_is_in_requirements(self):
        """gunicorn is listed in requirements.txt (WSGI-1)."""
        text = (REPO_ROOT / "requirements.txt").read_text().lower()
        self.assertIn("gunicorn", text)

    def test_dockerfile_runs_gunicorn_with_config(self):
        """The Dockerfile starts Gunicorn with -c gunicorn_config.py (DOC-3)."""
        text = (REPO_ROOT / "Dockerfile").read_text()
        self.assertIn('CMD ["gunicorn", "-c", "./gunicorn_config.py"]', text)


if __name__ == "__main__":
    unittest.main()
