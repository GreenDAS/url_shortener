# Final Demo Checklist (URL-21, SUB-3)

Author: Daniel S. | Date: 11/25/2026 | Version: V1.0

The course gives no credit without the 30 minute live demo, held during
finals week on my own laptop. The grade tiers stack, so the demo goes in
tier order: show Tier 1 working before moving on, and if something breaks
in a later tier the earlier tiers still count.

| Tier | Weight | What has to work | Spec IDs |
|---|---|---|---|
| 1 | 75% | App runs locally without Docker or Apache (`flask run` and Gunicorn) | PRE-1..5, WSGI-1..5 |
| 2 | 15% | App runs in the Docker container and reads and writes the host MySQL | DOC-1..7, DB-1..5 |
| 3 | 10% | App works through Apache at `http://url.short.com` | DNS-1..3, APA-1..8 |

Laptop paths: repo `C:\College\CSC\203\url_shortener`, XAMPP `C:\xampp`,
MySQL 8.4 `C:\Program Files\MySQL\MySQL Server 8.4`.

## 0. Before the Demo (the Day Before)

- [ ] `git pull` on `main` so the laptop matches GitHub (SUB-1).
- [ ] MySQL 8.4 is running (Services, or start `mysqld` by hand). Do NOT
      start XAMPP's MySQL, it would fight over port 3306.
- [ ] Docker Desktop is running.
- [ ] Run every step below once, start to finish, so nothing is a surprise.
- [ ] Make one or two short links ahead of time to have data to show, and
      know one long URL to paste live (e.g. `https://www.geneva.edu`).
- [ ] Stop the container afterwards (`docker compose down`) so Tier 1 starts
      from a clean slate.

## 1. Tier 1 (75%): Local, No Docker, No Apache

Open the repo folder in VS Code and a PowerShell terminal in it.

1. **Virtual environment and packages (PRE-2, PRE-3).**
   ```powershell
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
   Point out that `requirements.txt` pins Flask, PyMySQL, Gunicorn and
   python-dotenv (WSGI-1).
2. **Unit tests.** `python -m unittest` (or the VS Code Testing panel).
   Expect every test to pass.
3. **Flask dev server (PRE-4).** Point this one terminal at the laptop's
   MySQL and at the local address, so the short links on the page are
   clickable without Apache:
   ```powershell
   $env:MYSQL_HOST="127.0.0.1"
   $env:SITE_URL="http://127.0.0.1:5000"
   flask --app url_shortener run
   ```
   Open `http://127.0.0.1:5000/`, pick or add a user, shorten a URL (once
   random, once with a custom alias), click the short link and show the
   redirect, then delete a link. Ctrl+C to stop.
4. **Gunicorn (WSGI-2..5).** Gunicorn does not run on Windows itself (it
   needs Unix), so run it from WSL (Ubuntu) in the same repo folder:
   ```bash
   cd /mnt/c/College/CSC/203/url_shortener
   python3 -m venv .venv-wsl && source .venv-wsl/bin/activate
   pip install -r requirements.txt
   export MYSQL_HOST=$(ip route show default | awk '{print $3}')
   export SITE_URL=http://127.0.0.1:5000
   gunicorn -c ./gunicorn_config.py
   ```
   The `ip route` line finds the Windows host's address from inside WSL,
   since `127.0.0.1` in WSL is not Windows. Point out `bind = 0.0.0.0:5000`
   (WSGI-3, WSGI-4) and `wsgi_app = "url_shortener:app"` (WSGI-2) in
   `gunicorn_config.py`, then load `http://127.0.0.1:5000/` in the browser.
   Ctrl+C to stop. `make_submission.py` leaves `.venv-wsl` out of the zip.

## 2. Tier 2 (15%): Docker With the Host Database

1. **Build and start (DOC-1, DOC-3, DOC-4).**
   ```powershell
   docker compose up --build -d
   docker ps
   ```
   Point out the `Dockerfile` (system packages for the MySQL client, DOC-2)
   and that MySQL is NOT a container (DB-1).
2. **Logs (DOC-6).** `docker logs -f url_shortener_web`, then load a page
   and show the access log line appear.
3. **Database through host.docker.internal (DOC-5, DB-2..4).** Open
   `http://127.0.0.1:5000/` (DOC-7), make a link, then show it is in the
   laptop's MySQL:
   ```powershell
   & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -e "SELECT code, long_url FROM url_shortener.urls;"
   ```
   Mention the app's own `url_shortener@'%'` user (DB-3, DB-4) and that
   `.env` changes need `docker compose up --build -d` (DB-5).

## 3. Tier 3 (10%): Apache at url.short.com

1. **Hosts file (DNS-2, DNS-3).** Show the line `127.0.0.1 url.short.com`
   in `C:\Windows\System32\drivers\etc\hosts`, then `ping url.short.com`.
2. **Apache modules and vhost (APA-1..6).** Show in
   `C:\xampp\apache\conf\httpd.conf` the uncommented `proxy_module`,
   `proxy_http_module` and `headers_module` lines, and the `url.short.com`
   `<VirtualHost *:80>` in `conf\extra\httpd-vhosts.conf` (own logs,
   `ProxyPass` / `ProxyPassReverse` to `host.docker.internal:5000`,
   `RequestHeader set X-Forwarded-Proto "http"`). Optional:
   `C:\xampp\apache\bin\httpd.exe -M | findstr proxy`.
3. **Use the site (APA-7, APA-8).** Apache running in the XAMPP Control
   Panel, then open `http://url.short.com`, shorten a URL and click the
   `http://url.short.com/<code>` link.

## 4. If Something Breaks

| Symptom | Fix |
|---|---|
| `2003 Can't connect` | MySQL isn't running, or `MYSQL_HOST` is wrong for where the app runs (see [host-mysql.md](specs/host-mysql.md)) |
| `1045 Access denied` | `.env` user or password doesn't match the MySQL user |
| Tables missing | `flask --app url_shortener init-db` |
| Short link goes to url.short.com during Tier 1 | `$env:SITE_URL` wasn't set in that terminal |
| `url.short.com` shows the XAMPP dashboard or 503 | The container isn't running, or Apache wasn't restarted after a config change |
| Port 5000 in use | A `flask run` or Gunicorn from an earlier tier is still running |

## 5. Submission Steps (SUB-1, SUB-2)

1. Everything merged to `main` and pushed: https://github.com/GreenDAS/url_shortener
2. Build the zip: `python make_submission.py` (see
   [submission.md](specs/submission.md)). It lands at
   `C:\College\CSC\203\url_shortener_submission.zip` without `.venv` or `.env`.
3. Upload the zip and the GitHub link to eLearning.
4. Schedule the demo slot.
