# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: app/db.py
# Version: V1.2
# Description: Opens and closes the MySQL connection for each request and
#              adds the "flask init-db" command that builds the tables.
#
#              How a request uses the database:
#                1. Code in users.py or urls.py calls get_db().
#                2. The first call in a request opens a PyMySQL connection
#                   and keeps it on Flask's "g" object (one per request).
#                   Later calls in the same request get that same connection.
#                3. When the request ends, Flask calls close_db(), which
#                   closes it. init_app() is what tells Flask to do that.
#              Settings are read from app.config only. app/config.py is the
#              one place that reads .env / the environment and holds the
#              defaults (URL-26), so the two files can't disagree.
#              "flask --app url_shortener init-db" runs app/schema.sql.
#              Spec sheet: docs/specs/database.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
from importlib import resources  # Finds schema.sql Inside The app Package

import click  # Flask's Command Line Tool Is Built On Click
import pymysql  # Pure Python MySQL Driver
from flask import current_app, g  # current_app = The Running App, g = Per Request Storage

# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------
def connection_settings():
    """
    Collects everything pymysql.connect() needs, in one place so tests can
    check the values without opening a real connection. The MYSQL_* values
    come straight from app.config, which app/config.py's load_config()
    always fills in (with its defaults when .env leaves one out).
    Returns: dict of keyword args for pymysql.connect() (host, port, user,
             password, database, charset, cursorclass, autocommit)
    Raises: KeyError if a MYSQL_* key is missing from app.config,
            ValueError if MYSQL_PORT is not a number
    """
    config = current_app.config  # Filled Once At Startup By app/config.py
    return {
        "host": config["MYSQL_HOST"],
        "port": int(config["MYSQL_PORT"]),  # Already An int From load_config(), int() Covers A String Set By Hand
        "user": config["MYSQL_USER"],
        "password": config["MYSQL_PASSWORD"],
        "database": config["MYSQL_DB"],
        "charset": "utf8mb4",  # Full Unicode, Matches The Tables In schema.sql
        "cursorclass": pymysql.cursors.DictCursor,  # Rows Come Back As Dicts, Not Tuples
        "autocommit": False,  # Writers Call commit() Themselves
    }


def get_db():
    """
    Gets the MySQL connection for the current request, opening it on first use.
    Must be called inside a Flask app or request context, since it uses "g".
    Returns: pymysql Connection (the same one for the rest of the request)
    Raises: pymysql.err.OperationalError if MySQL can't be reached
    """
    if "db" not in g:  # First Call In This Request
        g.db = pymysql.connect(**connection_settings())
    return g.db


def close_db(error=None):
    """
    Closes the request's connection if one was opened. Flask calls this at the
    end of every request (and app context), even if the request crashed.
    Arg1 = error, the exception that ended the request (unused, Flask passes it)
    Returns: Nothing
    """
    db = g.pop("db", None)  # Take It Off "g" So It Can't Be Reused After Closing
    if db is not None:  # Requests That Never Touched The Database Have Nothing To Close
        db.close()


def split_sql_statements(script):
    """
    Breaks a .sql file into single statements, since PyMySQL runs one at a time.

    Steps:
      1. Go line by line and cut off anything after "--" (a SQL comment).
      2. Drop lines that are now empty.
      3. Join what is left into one long string and split it on ";".
      4. Squash runs of spaces so each statement is one tidy line.
    Note: this is a simple splitter for our own schema.sql. It does not
    handle "--" or ";" inside quoted strings, which schema.sql never has.

    Arg1 = script, the text of the .sql file
    Returns: list of statements with comments and blank lines removed
    """
    lines = []
    for line in script.splitlines():
        code = line.split("--", 1)[0].rstrip()  # Drop "-- comments" At The End Of A Line
        if code.strip():  # Skip Lines That Were Only A Comment Or Blank
            lines.append(code)
    statements = " ".join(lines).split(";")  # One Entry Per Statement (Last One Is Empty)
    return [" ".join(s.split()) for s in statements if s.strip()]  # Squash Extra Whitespace


def init_db():
    """
    Runs app/schema.sql against MySQL. Safe to run again since every table
    uses CREATE TABLE IF NOT EXISTS, so existing tables and rows are kept.
    Returns: number of statements that were run
    Raises: pymysql errors if MySQL can't be reached or a statement fails
    """
    script = resources.files("app").joinpath("schema.sql").read_text(encoding="utf-8")  # Works From Any Working Folder
    statements = split_sql_statements(script)

    db = get_db()
    with db.cursor() as cursor:  # Cursor Closes Itself At The End Of The "with"
        for statement in statements:
            cursor.execute(statement)
    db.commit()  # Autocommit Is Off, So Save The Changes
    return len(statements)


# The "flask init-db" command. Click shows this function's docstring as the
# command's --help text, so the docstring is kept to one line and the details
# live in this comment instead. Flask runs CLI commands inside an app
# context, so get_db() works here. Returns: Nothing, prints how many
# statements were run.
@click.command("init-db")
def init_db_command():
    """Creates the MySQL tables from app/schema.sql."""
    count = init_db()
    click.echo(f"Initialized the database ({count} statement(s) run).")


def init_app(app):
    """
    Hooks the database into the Flask app. app/__init__.py calls this once
    at startup, right after the config is loaded.
    Arg1 = app, the Flask app object
    Returns: Nothing
    """
    app.teardown_appcontext(close_db)  # Close The Connection After Every Request
    app.cli.add_command(init_db_command)  # Adds "flask init-db"
