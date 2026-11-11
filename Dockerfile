# ----------------------------------------------------------------------------
# Author: Daniel S.
# Date: 11/10/2026
# File: Dockerfile
# Version: V1.1
# Description: Builds the app image: Python, the app, its packages and
#              Gunicorn (spec DOC-1..7). Rebuild after any .env change (DB-5).
# ----------------------------------------------------------------------------
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System Packages The MySQL Client Library Needs (DOC-2)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies The App And The .env File Into The Image
COPY . .

EXPOSE 5000

# Gunicorn Serves The App, Settings Come From gunicorn_config.py (DOC-3)
CMD ["gunicorn", "-c", "./gunicorn_config.py"]
