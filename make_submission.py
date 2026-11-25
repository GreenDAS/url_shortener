# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/25/2026
# File: make_submission.py
# Version: V1.0
# Description: Builds the zip file that gets uploaded to eLearning for the
#              final submission (spec SUB-2, Jira URL-21).
#
#              The course asks for the project folder zipped WITHOUT the
#              virtual environment. This script also leaves out anything
#              that holds passwords (.env), Git's own history (.git, the
#              grader gets that from the GitHub link instead, SUB-1),
#              Python's compiled cache and any older submission zips.
#              Everything else in the repo folder goes in, kept under one
#              top level folder named "url_shortener" so it unzips cleanly.
#
#              Run from the repo folder with the venv active (or any Python):
#                python make_submission.py
#              The zip lands next to the repo folder by default, so it is
#              never zipped into itself. Use --out to pick another path.
#              Spec sheet: docs/specs/submission.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import argparse  # Reads The --out Option From The Command Line
import zipfile  # Python's Built In Zip Writer, No Extra Package Needed
from pathlib import Path  # Folder And File Paths That Work On Windows And Linux

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent  # The Folder This Script Lives In = The Repo Folder
ZIP_ROOT = "url_shortener"  # Top Level Folder Name Inside The Zip
DEFAULT_ZIP_NAME = "url_shortener_submission.zip"  # File Name When --out Isn't Given

# Folders Skipped Anywhere They Appear (Matched On The Folder Name)
EXCLUDED_DIRS = {
    ".venv", ".venv-wsl", "venv", "env",  # Virtual Environments (.venv-wsl Is The Gunicorn Demo One), The Spec Says Leave These Out (SUB-2)
    ".git",  # Git History, The Grader Uses The GitHub Link (SUB-1)
    "__pycache__",  # Python's Compiled Cache, Rebuilt Automatically
    ".pytest_cache", ".mypy_cache",  # Tool Caches, Not Part Of The Project
}

# Single Files Skipped Anywhere They Appear (Matched On The File Name)
EXCLUDED_FILES = {
    ".env",  # Real Passwords, Only .env.example Is Shared
}

# File Endings Skipped Anywhere They Appear
EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo",  # Compiled Python Files
    ".zip",  # Older Submission Zips, So A Zip Never Ends Up Inside The Next One
}

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def is_excluded(relative_path):
    """
    Decides if one file should be left out of the zip. A file is skipped
    when any folder on its path is an excluded folder, or the file's own
    name or ending is on an excluded list.
    Arg1 = relative_path, the file's path relative to the repo folder (a Path)
    Returns: True if the file should be left out, False if it goes in the zip
    """
    *folders, name = relative_path.parts  # Splits "app/templates/home.html" Into Folders And File Name
    if any(folder in EXCLUDED_DIRS for folder in folders):  # Inside .venv, .git, __pycache__ ...
        return True
    if name in EXCLUDED_FILES:  # .env
        return True
    return relative_path.suffix.lower() in EXCLUDED_SUFFIXES  # .pyc, .zip ...


def collect_files(repo):
    """
    Walks the whole repo folder and lists every file that belongs in the
    submission, sorted so the zip comes out the same every time.
    Arg1 = repo, the repo folder to walk (a Path)
    Returns: A sorted list of file paths relative to repo
    """
    files = []
    for path in repo.rglob("*"):  # Every File And Folder, At Any Depth
        if not path.is_file():  # Folders Are Created Inside The Zip From The File Paths
            continue
        relative = path.relative_to(repo)
        if not is_excluded(relative):
            files.append(relative)
    return sorted(files)


def build_zip(repo, zip_path):
    """
    Writes the submission zip. Every collected file goes in under the
    ZIP_ROOT folder, compressed with the normal zip (deflate) method that
    Windows Explorer can open.
    Arg1 = repo, the repo folder to zip (a Path)
    Arg2 = zip_path, where to write the zip file (a Path)
    Returns: The list of relative file paths that were put in the zip
    """
    files = collect_files(repo)
    zip_path.parent.mkdir(parents=True, exist_ok=True)  # Makes The Output Folder If Needed
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in files:
            archive.write(repo / relative, f"{ZIP_ROOT}/{relative.as_posix()}")  # Forward Slashes Inside Zips
    return files


def main(argv=None):
    """
    Command line entry point. Reads --out, builds the zip and prints a
    short report so it is easy to check .venv and .env were left out.
    Arg1 = argv, the command line arguments (None means the real ones)
    Returns: 0 when the zip was written
    """
    parser = argparse.ArgumentParser(description="Zip the project for the eLearning submission (SUB-2).")
    parser.add_argument("--out", type=Path, default=REPO.parent / DEFAULT_ZIP_NAME,
                        help=f"where to write the zip (default: ../{DEFAULT_ZIP_NAME})")
    args = parser.parse_args(argv)

    files = build_zip(REPO, args.out)
    print(f"Wrote {len(files)} files to {args.out.resolve()}")
    print("Left out: virtual environments, .env, .git, __pycache__, *.pyc and older zips")
    return 0


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    raise SystemExit(main())
