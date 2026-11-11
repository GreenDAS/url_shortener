# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: tests/test_docs.py
# Version: V1.0
# Description: Unit tests that keep the documentation rule from slipping.
#              Checks every Python file in app/ (plus url_shortener.py and
#              gunicorn_config.py) has the CPE-490 style header block and a
#              link to its spec sheet, every function and class has a
#              docstring, and every spec sheet exists and has at least one
#              Mermaid flow chart. Reads files only, no app or MySQL needed.
#              Run just this file: python -m unittest tests.test_docs -v
#              Spec sheet: docs/README.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import ast  # Parses Python Files Without Running Them
import re
import unittest
from pathlib import Path

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent  # tests/ -> Repo Folder
SPECS = REPO / "docs" / "specs"

# Every App Code File That Must Be Documented
CODE_FILES = sorted(REPO.glob("app/*.py")) + [REPO / "url_shortener.py", REPO / "gunicorn_config.py"]

# Header Fields From The CPE-490 Style, In Order
HEADER_FIELDS = ("# Author:", "# Date:", "# File:", "# Version:", "# Description:")

# ----------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------
class TestCodeHeaders(unittest.TestCase):
    """Checks each code file starts with the header block and names its spec sheet."""

    def test_header_fields_present(self):
        """The first lines have Author, Date, File, Version and Description."""
        for path in CODE_FILES:
            with self.subTest(file=path.name):
                top = path.read_text(encoding="utf-8").splitlines()[:8]
                for field in HEADER_FIELDS:
                    self.assertTrue(any(line.startswith(field) for line in top), f"{field} missing")

    def test_header_file_name_matches(self):
        """The File: line names the file it is in."""
        for path in CODE_FILES:
            with self.subTest(file=path.name):
                self.assertIn(f"# File: {path.relative_to(REPO).as_posix()}", path.read_text(encoding="utf-8"))

    def test_spec_sheet_linked_and_exists(self):
        """The header points at a spec sheet in docs/specs/ that really exists."""
        for path in CODE_FILES:
            with self.subTest(file=path.name):
                match = re.search(r"Spec sheet: (docs/specs/[\w-]+\.md)", path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match, "no 'Spec sheet:' line")
                self.assertTrue((REPO / match.group(1)).is_file(), f"{match.group(1)} not found")


class TestDocstrings(unittest.TestCase):
    """Checks every function and class has a docstring."""

    def test_every_function_and_class_documented(self):
        """ast finds no FunctionDef or ClassDef without a docstring."""
        for path in CODE_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    with self.subTest(file=path.name, name=node.name):
                        self.assertTrue(ast.get_docstring(node), "missing docstring")


class TestSpecSheets(unittest.TestCase):
    """Checks the spec sheets in docs/specs/ have their sections and charts."""

    def test_spec_sheets_exist(self):
        """There is at least one spec sheet."""
        self.assertTrue(list(SPECS.glob("*.md")))

    def test_each_spec_has_flow_chart(self):
        """Every spec sheet has at least one Mermaid block."""
        for path in SPECS.glob("*.md"):
            with self.subTest(spec=path.name):
                self.assertIn("```mermaid", path.read_text(encoding="utf-8"))

    def test_each_spec_has_core_sections(self):
        """Every spec sheet covers purpose, inputs, outputs, behavior and tests."""
        for path in SPECS.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for section in ("Purpose", "Inputs", "Outputs", "Behavior", "Tests"):
                with self.subTest(spec=path.name, section=section):
                    self.assertRegex(text, rf"## \d+\. {section}")

    def test_readme_links_every_spec(self):
        """docs/README.md links to every spec sheet."""
        readme = (REPO / "docs" / "README.md").read_text(encoding="utf-8")
        for path in SPECS.glob("*.md"):
            with self.subTest(spec=path.name):
                self.assertIn(f"specs/{path.name}", readme)


if __name__ == "__main__":
    unittest.main()
