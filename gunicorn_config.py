# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: gunicorn_config.py
# Version: V1.1
# Description: Gunicorn settings for serving the Flask app. Loaded with
#              "gunicorn -c ./gunicorn_config.py" (spec WSGI-1..5, DOC-3, DOC-6).
#
#              Gunicorn runs this file as plain Python and reads any
#              top level variable whose name matches one of its settings
#              (bind, workers, wsgi_app, accesslog, errorlog). Nothing here
#              is a function, so the names themselves are the interface.
#              The Dockerfile's CMD points Gunicorn at this file, and
#              compose.dev.yaml adds --reload and --workers 1 on top of it.
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------------
import multiprocessing  # cpu_count() For The Worker Formula
import os  # Lets The Environment Override The Port And Worker Count

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
port = int(os.environ.get("APP_PORT", "5000"))  # Student Selected Port (WSGI-4)

bind = f"0.0.0.0:{port}"  # 0.0.0.0 Accepts Requests From Any IP (WSGI-3), Needed In A Container
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))  # (2 x Cores) + 1
wsgi_app = "url_shortener:app"  # module:variable Of The Flask App (WSGI-2)

accesslog = "-"  # Access Log To stdout So "docker logs" Shows Requests (DOC-6)
errorlog = "-"  # Error Log To stderr (DOC-6)
