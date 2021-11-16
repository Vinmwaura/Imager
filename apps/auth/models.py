import os
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
        return "<Permission %s>" % self.permission


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

    def create_salt(self, salt_len=16):
        """
        Creates a salt of 16 bytes(Default)
        Args:
          salt_len: Length in bytes of the salt to be generated.

        Returns:
          Salt value.
        """
        from bcrypt import gensalt
        return gensalt(salt_len)

    def hash_password(self, salt, password):
        """
        Hashes password using salt

        Args:
          salt: Salt value.
          password: Plain-text password

        Returns:
          Hashed password.
        """
        from bcrypt import hashpw
        hashed_pwd = hashpw(
            password,
            salt)
        return hashed_pwd

    def generate_salt_pwd(self, password):
        """
        Generates salt and hashed password

        Args:
          password: Plain-text password

        Returns:
          Salt and Hashed password.
        """
        try:
            # Get salt
            salt = self.create_salt()

            # Hash password using salt
            pwd_hash = self.hash_password(
                salt,
                password.encode("utf-8"))

            return salt, pwd_hash
        except Exception as e:
            raise e

    def add_user(self, user_dict):
        """
        Adds User to the database.

        Args:
          user_dict: Dictionary containing details about the user

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.username = user_dict['username']
            self.first_name = user_dict['first_name']
            self.last_name = user_dict['last_name']
            self.email = user_dict['email']
            self.user_role = user_dict['user_role']
            self.salt, self.password_hash = self.generate_salt_pwd(
                user_dict['password'])

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when creating user: {}".format(e))
            return False

    def __repr__(self):
        return "<User %s>" % self.username
