from flask import Flask

app = Flask(__name__)

from app import db
db.init_app(app)  # MySQL Connection + "flask init-db" Command

from app import routes
