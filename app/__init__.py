from flask import Flask
import firebase_admin
from firebase_admin import credentials

from . import config
from .utils import format_datetime


def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.jinja_env.filters["format_datetime"] = format_datetime

    # Firebase setup
    cred = credentials.Certificate(config.FIREBASE_CREDENTIALS)
    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": config.DATABASE_URL,
            "storageBucket": config.STORAGE_BUCKET,
        },
    )

    # Import and register the blueprint
    from . import routes

    app.register_blueprint(routes.bp)

    return app
