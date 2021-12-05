import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

from flask_mail import Mail

from flask_wtf.csrf import CSRFProtect


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATICFILES_DIRS = (os.path.join(
    BASE_DIR, "apps/static"),)
MEDIA_ROOT = os.path.join(
    BASE_DIR, "apps/media")

# Handles Database operations
db = SQLAlchemy()

# Handles Database migrations
migrate = Migrate()

# Handles Session management
login_manager = LoginManager()

# Handles sending of email
mail = Mail()

# Handles CSRF protection for AJAX requests
csrf = CSRFProtect()


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
        # Added to remove warnings
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
        app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
        app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL")
        app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
        app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
        app.config["MAIL_DEBUG"] = os.getenv("MAIL_DEBUG")

        app.config["MAX_CONTENT_LENGTH"] = os.getenv("MAX_CONTENT_LENGTH") or \
            1024 * 1024  # Max: 1MB in size
        app.config["UPLOAD_EXTENSIONS"] = os.getenv("UPLOAD_EXTENSIONS") or \
            [".jpg", ".png", ".jpeg"]
        app.config["UPLOAD_PATH"] = os.getenv("UPLOAD_PATH") or \
            os.path.join(
                MEDIA_ROOT,
                "user_uploads")

        app.config["TEST_EMAIL_CONFIG"] = os.getenv("TEST_EMAIL_CONFIG")

    # Apps Blueprint Registration
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .admin_panel import admin_panel_bp
    app.register_blueprint(admin_panel_bp)

    from .imager import imager_bp
    app.register_blueprint(imager_bp)

    # Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    return app
