test_config = {
    "SECRET_KEY": "Testing123",
    "FLASK_ENV": "testing",
    "ENV": "testing",
    "WTF_CSRF_ENABLED": False,
    "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2://unittestuser:password@localhost/unittestdb",
    "SQLALCHEMY_TRACK_MODIFICATIONS": True,
    "DEBUG": False,
    "TESTING": True,
}