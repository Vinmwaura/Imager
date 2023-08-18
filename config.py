import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATICFILES_DIRS = (os.path.join(
    BASE_DIR, "apps/static"),)
MEDIA_ROOT = os.path.join(
    BASE_DIR, "apps/media")

# Loads .env variables if any.
env_file = ".env"
env = os.path.join(os.getcwd(), env_file)
if os.path.exists(env):
    load_dotenv(env)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI")

    # Uploaded Image Config.
    MAX_CONTENT_LENGTH = os.getenv("MAX_CONTENT_LENGTH") or \
        1024 * 1024  # Max: 1MB in size
    UPLOAD_EXTENSIONS = os.getenv("UPLOAD_EXTENSIONS") or \
        [".jpg", ".png", ".jpeg"]
    UPLOAD_PATH = os.getenv("UPLOAD_PATH") or \
        os.path.join(
            MEDIA_ROOT,
            "user_uploads")


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    FLASK_ENV = "production"
    TEST_EMAIL_CONFIG = None

    # MAIL Config
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEBUG = os.getenv("MAIL_DEBUG")

    # API configurations.
    API_PER_PAGE = os.getenv("API_PER_PAGE") or 20
    API_MAX_PER_PAGE = os.getenv("API_MAX_PER_PAGE") or 50
    OAUTH2_REFRESH_TOKEN_GENERATOR = os.getenv(
        "OAUTH2_REFRESH_TOKEN_GENERATOR") or True

    # Added to remove warnings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    FLASK_ENV = "development"
    TEST_EMAIL_CONFIG = None

    # MAIL Config
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEBUG = os.getenv("MAIL_DEBUG")

    # API configurations.
    API_PER_PAGE = os.getenv("API_PER_PAGE") or 20
    API_MAX_PER_PAGE = os.getenv("API_MAX_PER_PAGE") or 50
    OAUTH2_REFRESH_TOKEN_GENERATOR = os.getenv(
        "OAUTH2_REFRESH_TOKEN_GENERATOR") or True

    # Added to remove warnings
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    FLASK_ENV = "testing"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_SQLALCHEMY_DATABASE_URI")
    TEST_EMAIL_CONFIG = os.getenv(
        "TEST_EMAIL_CONFIG",
        None)
    
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = True
