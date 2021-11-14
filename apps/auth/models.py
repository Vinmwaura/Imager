from .. import db
from enum import Enum, auto


# Permissions Enums
class PermissionsEnum(Enum):
    CAN_ACCESS_ADMIN = auto()
    CAN_UPDATE_ADMIN = auto()
    CAN_INSERT_ADMIN = auto()
    CAN_POST_DASHBOARD = auto()
    CAN_VIEW_DASHBOARD = auto()


# Permission Table
class Permissions(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permission = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return "<Permission %s>" % self.id


# Role Table
class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    permissions = db.relationship(
        "Permissions",
        backref="role",
        lazy='dynamic')

    def __repr__(self):
        return "<Role %s>" % self.name


# User Table
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)

    salt = db.Column(db.String(16), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    user_role = db.Column(db.Integer, db.ForeignKey('role.id'))

    active = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<User %s>" % self.username
