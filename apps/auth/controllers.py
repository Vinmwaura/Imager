from .. import db
from . import models
from .. import login_manager

from .auth import *

from .utils import (
    validate_names,
    validate_password)

from flask import current_app

from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired

from email_validator import validate_email, EmailNotValidError


# Tells Flask-login how to load users given an id.
@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))


def generate_token(email, token_type):
    """
    Generates token to be sent to User.

    Args:
      email: Email of User.
      token_type: Salt key used in creating the token.

    Returns:
      Token.
    """
    try:
        # SECRETS KEY in config.
        secret_key = current_app.config["SECRET_KEY"]
        timed_serializer = URLSafeTimedSerializer(secret_key)
        email_activation_token = timed_serializer.dumps(
            email,
            salt=token_type)
        return email_activation_token
    except Exception as e:
        print("An error occured when generating token: {}".format(e))
        return None


def validate_token(received_token, token_type, token_max_age):
    """
    Confirms if token is genuine and from the User Email.

    Args:
      received_token: Token.
      token_type: Salt key used in creating the token.

    Returns:
      User object who passed the token from their Email or None if errors
    """
    secret_key = current_app.config["SECRET_KEY"]
    timed_serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = timed_serializer.loads(
            received_token,
            salt=token_type,
            max_age=token_max_age)
        user = models.User.query.filter_by(email=email).one_or_none()
        return user, None
    except SignatureExpired:
        # return None, EXPIRED_SIGNATURE_TOKEN_ERROR
        return None, "expired-token"
    except BadSignature:
        # return None, BAD_SIGNATURE_TOKEN_ERROR
        return None, "bad-token"
    except Exception as e:
        print("An error occured while confirming token: {}".format(e))
        # return None, SERVER_ERROR
        return None, "server-error"


def confirm_email(user):
    """
    Activates user if not already activated.

    Args:
      user: User object.

    Returns:
      Boolean indicating if user was activated.
    """
    if not user.email_confirmed:
        status = user.confirm_email()
        if status:
            return status, None
        else:
            # return False, SERVER_ERROR
            return False, "server-error"
    else:
        # return False, EMAIL_ALREADY_CONFIRMED
        return False, "email-confirmed"


@validate_names
def change_username(user, new_username):
    """
    Changes Username.

    Args:
      user: User object.
      new_username: New username for client.

    Returns:
      Boolean indicating if username was changed.
    """
    status = user.change_username(new_username)
    return status


@validate_names
def change_firstname(user, new_firstname):
    """
    Changes Firstname of user.

    Args:
      user: User object.
      new_username: New username for client.

    Returns:
      Boolean indicating if email was changed.
    """
    status = user.change_firstname(new_firstname)
    return status


@validate_names
def change_lastname(user, new_lastname):
    """
    Changes Lastname of user.

    Args:
      user: User object.
      new_lastname: New last_name of user.

    Returns:
      Boolean indicating if email was changed.
    """
    status = user.change_lastname(new_lastname)
    return status


def change_user_email(user, new_email):
    """
    Changes User email and sends an authentication
    email to check if new email is legit.

    Args:
      user: User object.
      new_email: New email for client.

    Returns:
      Boolean indicating if email was changed.
    """
    try:
        # Attempts to validate if proper email, raises Exception if not
        validate_email(new_email)
        if user and user.active:
            status = user.change_email(new_email)
            return status, None
        else:
            return False, "invalid-user"
    except EmailNotValidError as e:
        print("Invalid Email: ", e)
        return False, "email-invalid"


@validate_password
def change_user_password(user, new_password):
    """
    Changes User password.

    Args:
      user: User object.
      password: Plain text password of new password.

    Returns:
      Boolean indicating if password was changed.
    """
    status = user.change_password(new_password)
    return status


def check_username_exists(username):
    """
    Checks if Username exists in User table.

    Args:
      username: Username string.

    Returns:
      Boolean indicating result of operation.
    """
    user_exists = models.User().query.filter_by(
        username=username).one_or_none()
    return user_exists


def check_email_exists(email):
    """
    Checks if Email exists in User table.

    Args:
      username: username

    Returns:
      Boolean indicating result of operation.
    """
    email_exists = models.User().query.filter_by(
        email=email).one_or_none()
    return email_exists


def get_Role(role_name):
    """
    Gets Role object using role_name passed.

    Args:
      role_name: Name for Role.

    Returns:
      Role object if any.
    """
    user_role = models.Role().query.filter_by(
        name=role_name).one_or_none()
    return user_role


def get_Permission(role):
    """
    Get Permission object(s).

    Args:
      role: Role object.

    Returns:
      List of Permissions if any.
    """
    role_permissions = models.Permissions().query.filter_by(
        role_id=role.id).all()
    return role_permissions


def add_Role(role_name):
    """
    Creates Role object and adds it to Session if no error occurs.

    Args:
      role_name: Name for Role.

    Returns:
      Boolean indicating result of operation.
    """
    try:
        user_role = models.Role(name=role_name)
        """
        Adds Role but doesn't commit so that the Permissions can
        be added together and if any error occurs,
        rollback all of it.
        """
        db.session.add(user_role)
        return user_role

    except Exception as e:
        # Rollback session
        db.session.rollback()

        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
        return None


def add_Permission(role_id, permission_index):
    """
    Creates Permission object and adds it to Session if no error occurs.

    Args:
      role_id: Id for Role
      permission_index: Index for permission in Enum Object

    Returns:
      Boolean indicating result of operation.
    """
    try:
        role_permission = models.Permissions(
            role_id=role_id,
            permission=permission_index)

        db.session.add(role_permission)
        return role_permission
    except Exception as e:
        # Rollback session
        db.session.rollback()

        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
        return None


def add_User(user_details):
    """
    Creates User.

    Args:
      user_details: Dictionary containing username, first_name,
                    last_name, email, and password.

    Returns:
      Boolean indicating result of operation.

    Raises:
      Exception: Any exeption that occurs when creating User.
    """
    try:
        user_created = models.User().add_user(user_details)
        return user_created
    except Exception as e:
        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
        return False


def search_by_username(search_value):
    """
    Search User model by username.

    Args:
      search_value: Search value.

    Returns:
      Username query results.
    """
    # user_ = models.User()
    search = "%{}%".format(search_value)
    usernames = db.session.query(models.User).filter(
        models.User.username.ilike(search)).all()
    return usernames


def account_creation(user_details, role_name, permissions=[]):
    """
    Creates User Account including Roles and Permissions if they don't exist.

    Args:
      user_details: Dictionary containing username, first_name,
                    last_name, email, and password.
      role_name: Name of role
      permissions: List of permissions from ENUM object

    Returns:
      Boolean indicating result of operation.

    Raises:
      Exception: Any exeption that occurs when commiting
      User, Role and Permissions.
    """
    
    # Create User Role if none exists
    user_role = get_Role(role_name=role_name)
    if user_role is None:
        user_role = add_Role(role_name)
        if not user_role:
            print("Role {} was not able to be created.".format(role_name))
            return False

    # Add User Permissions to User Role if none exists
    role_permissions = get_Permission(user_role)
    if not role_permissions:
        for permission in permissions:
            role_permissions = add_Permission(
                role_id=user_role.id,
                permission_index=permission.value)

    """
    Commit Roles and Permissions added
    Allows rolling back both Roles and Permission
    if an error occurs while commiting either one
    """
    try:
        db.session.commit()
    except Exception as e:
        # Rollback session
        db.session.rollback()

        print("An error occured while committing: {}".format(e))

        return False

    # Appends User Role to user details Dict
    user_details["user_role"] = user_role.id

    # Create Admin User
    user_created = add_User(user_details)
    if user_created:
        # TODO: Log messages.
        """
        print("User: {} has been successfully added".format(
            user_details["username"]))
        """
        return True
    else:
        return False


def authenticate_user(username_email, password):
    """
    Authenticates User account given username, and password.

    Args:
      username: Username.
      password: Password in plaintext.

    Returns:
      Boolean indicating result of operation.
    """
    try:
        # Attempts to validate if email was used in login.
        validate_email(username_email)

        user_ = models.User().query.filter_by(
            email=username_email).first()
    except EmailNotValidError:
        # Assumes username was used.
        user_ = models.User().query.filter_by(
            username=username_email).first()

    if user_:
        user_authenticated = user_.check_hash(password)
        if user_authenticated:
            return user_
        else:
            return None
    else:
        return None
