import os
from dotenv import load_dotenv

# Loads .env variables if any.
env_file = ".env"
env = os.path.join(os.getcwd(), env_file)
if os.path.exists(env):
    load_dotenv(env)

test_config = {
    "SECRET_KEY": os.environ.get("SECRET_KEY"),
    "FLASK_ENV": "testing",
    "ENV": "testing",
    "WTF_CSRF_ENABLED": False,
    "SQLALCHEMY_DATABASE_URI": os.environ.get("TESTING_SQLALCHEMY_DATABASE_URI"),
    "SQLALCHEMY_TRACK_MODIFICATIONS": True,
    "DEBUG": False,
    "TESTING": True,
}

