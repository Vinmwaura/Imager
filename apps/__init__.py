import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Handles Database operations
db = SQLAlchemy()


def create_app(config=None):
    app = Flask(__name__)

    # Load Configuration variables
    if config:
        try:
            app.config.from_mapping(config)
        except Exception as e:
            print("Error occured loading config from mapping: {}".format(e))
    else:
        from dotenv import load_dotenv
        load_dotenv()  # Take environment variables from .env.

        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
        app.config["DEBUG"] = os.getenv("DEBUG")
        app.config["FLASK_ENV"] = os.getenv("FLASK_ENV")
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
            "SQLALCHEMY_DATABASE_URI")

    # Flask extensions
    db.init_app(app)

    # Apps Blueprint Registration
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    return app
