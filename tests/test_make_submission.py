# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/25/2026
# File: tests/test_make_submission.py
# Version: V1.0
# Description: Unit tests for make_submission.py (the eLearning zip, SUB-2).
#
#              Builds a small fake project in a temporary folder with a
#              .venv, a .env, a .git folder, __pycache__ and a .pyc file,
#              zips it, and checks only the real project files went in.
#              No app or MySQL needed.
#              Run just this file: python -m unittest tests.test_make_submission -v
#              Spec sheet: docs/specs/submission.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import io
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path, PurePosixPath

import make_submission

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
KEPT = ["url_shortener.py", "requirements.txt", ".env.example", "app/__init__.py",
        "app/templates/home.html", "docs/specs/redirect.md", "tests/test_urls.py"]
DROPPED = [".env", ".venv/Scripts/python.exe", "venv/lib/site.py", ".git/HEAD",
           "app/__pycache__/urls.cpython-315.pyc", "stray.pyc", "old_submission.zip"]

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestIsExcluded(unittest.TestCase):
    """Checks the rule that decides which single files are left out."""

    def test_project_files_are_kept(self):
        """Normal code, docs and the .env.example template go in."""
        for name in KEPT:
            with self.subTest(file=name):
                self.assertFalse(make_submission.is_excluded(PurePosixPath(name)))

    def test_secret_and_generated_files_are_dropped(self):
        """.env, venvs, .git, caches, .pyc and old zips stay out."""
        for name in DROPPED:
            with self.subTest(file=name):
                self.assertTrue(make_submission.is_excluded(PurePosixPath(name)))

    def test_env_example_is_not_mistaken_for_env(self):
        """Only the exact name .env is a secret, .env.example is the shared template."""
        self.assertFalse(make_submission.is_excluded(PurePosixPath(".env.example")))
        self.assertTrue(make_submission.is_excluded(PurePosixPath("sub/.env")))


class TestBuildZip(unittest.TestCase):
    """Zips a fake project folder and looks inside the result."""

    def setUp(self):
        """Makes a temporary repo folder holding every KEPT and DROPPED file."""
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        for name in KEPT + DROPPED:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"contents of {name}", encoding="utf-8")
        self.zip_path = self.root / "out" / "submission.zip"  # "out" Doesn't Exist Yet On Purpose

    def tearDown(self):
        """Deletes the temporary folder."""
        self.temp.cleanup()

    def test_zip_holds_exactly_the_kept_files(self):
        """The zip lists every KEPT file under url_shortener/ and nothing else."""
        make_submission.build_zip(self.repo, self.zip_path)
        with zipfile.ZipFile(self.zip_path) as archive:
            names = sorted(archive.namelist())
        self.assertEqual(names, sorted(f"url_shortener/{name}" for name in KEPT))

    def test_file_contents_survive(self):
        """A file read back out of the zip matches what was written."""
        make_submission.build_zip(self.repo, self.zip_path)
        with zipfile.ZipFile(self.zip_path) as archive:
            self.assertEqual(archive.read("url_shortener/app/__init__.py").decode(), "contents of app/__init__.py")

    def test_returns_sorted_file_list(self):
        """build_zip() returns the same files it zipped, in sorted order."""
        files = make_submission.build_zip(self.repo, self.zip_path)
        self.assertEqual([f.as_posix() for f in files], sorted(KEPT))

    def test_main_writes_to_out_and_reports(self):
        """main() with --out writes the zip there and prints the file count."""
        original = make_submission.REPO
        make_submission.REPO = self.repo  # Points The Script At The Fake Repo
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                result = make_submission.main(["--out", str(self.zip_path)])
        finally:
            make_submission.REPO = original
        self.assertEqual(result, 0)
        self.assertTrue(self.zip_path.is_file())
        self.assertIn(f"Wrote {len(KEPT)} files", output.getvalue())


if __name__ == "__main__":
    unittest.main()
