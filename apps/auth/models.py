from .. import db
from enum import Enum, auto

from flask_login import UserMixin

from .auth import *


# Permissions Enums
class PermissionsEnum(Enum):
    CAN_VIEW_ADMIN = auto()
    CAN_UPDATE_ADMIN = auto()
    CAN_INSERT_ADMIN = auto()
    CAN_DELETE_ADMIN = auto()
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
        lazy='joined')

    def __repr__(self):
        return "<Role %s>" % self.name


# User Table
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)

    password_hash = db.Column(db.String(128), nullable=False)

    user_role = db.Column(db.Integer, db.ForeignKey('role.id'))

    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    role = db.relationship(
        "Role",
        lazy='joined')

    def get_user_id(self):
        return self.id

    def is_active(self):
        """
        Gets active field value.

        Returns:
          Boolean indicating whether user is active.
        """
        return self.active

    def can_view_admin_dashboard(self):
        """
        Checks whether user has role with permission to view admin dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_VIEW_ADMIN.value).first()
        if permission:
            return True
        return False

    def can_update_admin_dashboard(self):
        """
        Checks whether user has role with permission to update admin dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_UPDATE_ADMIN.value).first()

        if permission:
            return True
        return False


    def can_delete_admin_dashboard(self):
        """
        Checks whether user has role with permission to delete from admin dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_DELETE_ADMIN.value).first()

        if permission:
            return True
        return False

    def can_insert_admin_dashboard(self):
        """
        Checks whether user has role with permission to insert
        records in admin dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_INSERT_ADMIN.value).first()
        if permission:
            return True
        return False

    def can_view_main_dashboard(self):
        """
        Checks whether user has role with permission to view main dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_VIEW_DASHBOARD.value).first()
        if permission:
            return True
        return False

    def can_post_main_dashboard(self):
        """
        Checks whether user has role with permission to post to main dashboard.

        Returns:
          Boolean value.
        """
        permission = Permissions.query.filter_by(
            role_id=self.user_role,
            permission=PermissionsEnum.CAN_POST_DASHBOARD.value).first()
        if permission:
            return True
        return False

    def check_hash(self, password):
        """
        Hashes password using salt and compares with hashed password.

        Args:
          password: Plain text password.

        Returns:
          Boolean value indicating result of comparison.
        """
        from bcrypt import checkpw
        input_pw = password.encode("utf-8")
        stored_pw = self.password_hash.encode("utf-8")
        return checkpw(
            input_pw,
            stored_pw)

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

    def confirm_email(self):
        """
        Confirm User Email.

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.email_confirmed = True

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print("Exception occured when confirming user email: {}".format(e))
            return False

    def activate_user(self):
        """
        Activates user account.

        Returns:
            Boolean indicating result of operation.
        """
        try:
            self.active = True

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True
        except Exception as e:
            print("An error occured while deactivating user", e)
            return False

    def deactivate_user(self):
        """
        Deactivates user account.

        Returns:
            Boolean indicating result of operation.
        """
        try:
            self.active = False

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True
        except Exception as e:
            print("An error occured while deactivating user", e)
            return False

    def change_username(self, new_username):
        """
        Changes username.

        Args:
          new_email: New Email.

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.username = new_username

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when updating username: {}".format(e))
            return False

    def change_firstname(self, new_firstname):
        """
        Changes first_name.

        Args:
          new_firstname: New first name.

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.first_name = new_firstname

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when updating first_name: {}".format(e))
            return False

    def change_lastname(self, new_lastname):
        """
        Changes last_name.

        Args:
          new_lastname: New last name.

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.last_name = new_lastname

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when updating last_name: {}".format(e))
            return False

    def change_email(self, new_email):
        """
        Changes email.

        Args:
          new_email: New Email.

        Returns:
          Boolean indicating result of operation.
        """
        try:
            self.email = new_email

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when updating email: {}".format(e))
            return False

    def change_password(self, new_password):
        """
        Changes password.

        Args:
          password: New password

        Returns:
          Boolean indicating result of operation.
        """
        try:
            # Create salt
            salt = self.create_salt()

            # Hash password using salt created
            password_hash = self.hash_password(
                salt,
                new_password.encode("utf-8"))

            self.password_hash = password_hash.decode("utf-8")

            # Adds User object containing the user details
            db.session.add(self)

            # Commit session
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print("Exception occured when updating password: {}".format(e))
            return False

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
            if "email_confirmed" in user_dict:
                self.email_confirmed = user_dict['email_confirmed']

            # Create salt
            salt = self.create_salt()

            # Hash password using salt created
            password_hash = self.hash_password(
                salt,
                user_dict['password'].encode("utf-8"))

            self.password_hash = password_hash.decode("utf-8")

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
