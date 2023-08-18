import os

from flask import (
    Flask,
    render_template)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from flask_login import LoginManager

from flask_mail import Mail

from flask_wtf.csrf import CSRFProtect

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# Handles Database operations.
db = SQLAlchemy()

# Handles Database migrations.
migrate = Migrate()

# Handles Session management.
login_manager = LoginManager()

# Handles sending of email.
mail = Mail()

# Handles CSRF protection for AJAX requests.
csrf = CSRFProtect()

# Handles API Rate Limit.
limiter = Limiter(key_func=get_remote_address)


def unauthorized(e):
    return render_template('errors/401.html'), 401


def forbidden(e):
    return render_template('errors/403.html'), 403


def page_not_found(e):
    return render_template('errors/404.html'), 404


def request_entity_too_large_error(e):
    return render_template('errors/413.html'), 413


def internal_server_error(e):
    return render_template('errors/500.html'), 500


def create_app(config="config.DevelopmentConfig"):
    app = Flask(__name__)

    app.register_error_handler(401, unauthorized)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(413, request_entity_too_large_error)
    app.register_error_handler(500, internal_server_error)

    # Load Configuration variables
    app.config.from_object(config)

    # Apps Blueprint Registration.
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .admin_panel import admin_panel_bp
    app.register_blueprint(admin_panel_bp)

    from .imager import imager_bp
    app.register_blueprint(imager_bp)

    from .api import api_bp
    app.register_blueprint(api_bp)

    # Flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = 'auth.login'

    from .oauth2_config import config_oauth
    config_oauth(app)

    return app
