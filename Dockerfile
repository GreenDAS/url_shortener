# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/11/2026
# File: Dockerfile
# Version: V1.2
# Description: Builds the app image: Python, the app, its packages and
#              Gunicorn (spec DOC-1..7). Rebuild after any .env change (DB-5).
#
#              Build order is picked so Docker can reuse cached layers:
#              system packages and pip install only rerun when
#              requirements.txt changes, not on every code edit, because
#              requirements.txt is copied in before the rest of the code.
#              compose.yaml builds this image as the "web" service.
#              Spec sheet: docs/specs/app-startup.md
# ----------------------------------------------------------------------------
FROM python:3.15-slim
# Slim Debian Image With Python 3.15 Already Installed

# No .pyc Files In The Image, And print()/Logs Show Up Right Away In docker logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
# Every Path Below Is Inside /app In The Container

# System Packages The MySQL Client Library Needs (DOC-2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Packages (Flask, PyMySQL, Gunicorn, python-dotenv) Installed Before The Code Is Copied
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies The App And The .env File Into The Image
COPY . .

# Documents The Port Gunicorn Listens On (compose.yaml Publishes It)
EXPOSE 5000

# Gunicorn Serves The App, Settings Come From gunicorn_config.py (DOC-3)
CMD ["gunicorn", "-c", "./gunicorn_config.py"]
