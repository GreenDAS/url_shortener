from flask import Flask

app = Flask(__name__)
app.config.setdefault("SECRET_KEY", "dev-only-not-secret")  # Sessions Need A Key, app/config.py Sets The Real One

from app import db
db.init_app(app)  # MySQL Connection + "flask init-db" Command

from app import routes
from app import accounts  # noqa: E402  Switch User (URL-12)
