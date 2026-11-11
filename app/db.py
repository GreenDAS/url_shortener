# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: app/db.py
# Version: V1.0
# Description: Opens and closes the MySQL connection for each request and
#              adds the "flask init-db" command that builds the tables.
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import os
from importlib import resources

import click
import pymysql
from flask import current_app, g

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
DEFAULT_MYSQL_HOST = "127.0.0.1"  # Used When Nothing Is Set (flask run On The Laptop)
DEFAULT_MYSQL_PORT = 3307  # Port The MySQL Container Publishes On The Host
DEFAULT_MYSQL_DB = "url_shortener"

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def _setting(name, default):
    """
    Looks up one MySQL setting.
    Arg1 = name, the config key (e.g. "MYSQL_HOST")
    Arg2 = default, value to use if it is not set anywhere
    Returns: app.config value if set, Else: environment variable, Else: default
    """
    value = current_app.config.get(name)
    if value in (None, ""):
        value = os.environ.get(name, default)  # Fallback So This Works Before app/config.py Exists
    return value


def connection_settings():
    """
    Collects everything pymysql.connect() needs.
    Returns: dict of keyword args for pymysql.connect()
    """
    return {
        "host": _setting("MYSQL_HOST", DEFAULT_MYSQL_HOST),
        "port": int(_setting("MYSQL_PORT", DEFAULT_MYSQL_PORT)),
        "user": _setting("MYSQL_USER", ""),
        "password": _setting("MYSQL_PASSWORD", ""),
        "database": _setting("MYSQL_DB", DEFAULT_MYSQL_DB),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,  # Rows Come Back As Dicts, Not Tuples
        "autocommit": False,  # Writers Call commit() Themselves
    }


def get_db():
    """
    Gets the MySQL connection for the current request, opening it on first use.
    Returns: pymysql Connection (the same one for the rest of the request)
    """
    if "db" not in g:
        g.db = pymysql.connect(**connection_settings())
    return g.db


def close_db(error=None):
    """
    Closes the request's connection if one was opened. Flask calls this at the
    end of every request.
    Arg1 = error, the exception that ended the request (unused, Flask passes it)
    Returns: Nothing
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def split_sql_statements(script):
    """
    Breaks a .sql file into single statements, since PyMySQL runs one at a time.
    Arg1 = script, the text of the .sql file
    Returns: list of statements with comments and blank lines removed
    """
    lines = []
    for line in script.splitlines():
        code = line.split("--", 1)[0].rstrip()  # Drop "-- comments" At The End Of A Line
        if code.strip():
            lines.append(code)
    statements = " ".join(lines).split(";")
    return [" ".join(s.split()) for s in statements if s.strip()]  # Squash Extra Whitespace


def init_db():
    """
    Runs app/schema.sql against MySQL. Safe to run again since every table
    uses CREATE TABLE IF NOT EXISTS.
    Returns: number of statements that were run
    """
    script = resources.files("app").joinpath("schema.sql").read_text(encoding="utf-8")
    statements = split_sql_statements(script)

    db = get_db()
    with db.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
    db.commit()
    return len(statements)


@click.command("init-db")
def init_db_command():
    """Creates the MySQL tables from app/schema.sql."""
    count = init_db()
    click.echo(f"Initialized the database ({count} statement(s) run).")


def init_app(app):
    """
    Hooks the database into the Flask app.
    Arg1 = app, the Flask app object
    Returns: Nothing
    """
    app.teardown_appcontext(close_db)  # Close The Connection After Every Request
    app.cli.add_command(init_db_command)  # Adds "flask init-db"
