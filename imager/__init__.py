import os

from flask import Flask


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

    return app
