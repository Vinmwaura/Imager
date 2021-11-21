import os
import re
import click
from .. import db
from . import models
from . import auth_bp
from .. import login_manager

from flask import current_app

from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from email_validator import validate_email, EmailNotValidError


"""
Constants
"""
# Min and Max length of First and Last names
MIN_NAMES = 2
MAX_NAMES = 20

# Min and Max length of password
MIN_PASSWORD = 8
MAX_PASSWORD = 128

# Regex patterns constants
# Only single words consisting of numbers, letters, undercore(s) or hyphens
NAMES_REGEX = "^[a-zA-Z0-9-_]+$"

# Password regex:
# At least one upper case English letter, (?=.*?[A-Z])
# At least one lower case English letter, (?=.*?[a-z])
# At least one digit, (?=.*?[0-9])
# At least one special character, (?=.*?[#?!@$%^&*-])
PASSWORD_REGEX = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{4,}$$"

# Error Messages
PASSWORD_REQUIREMENTS = "Password has to have:\n\
    > At least one upper case English letter,\n\
    > At least one lower case English letter,\n\
    > At least one digit,\n\
    > At least one special character."
NAME_REQUIREMENTS = "Field must contain letters, numbers and underscores only."
INVALID_FIELD_LENGTH = lambda field_min, field_max: 'Field must be between {} and {} characters.'.format(
                        field_min, field_max)
USERNAME_ALREADY_EXISTS = lambda username: "Username {} already exists.".format(username)
USER_ALREADY_ACTIVE = "User has already confirmed their email"
EMAIL_ALREADY_USED = lambda email: "Email {} has been used by another account.".format(email)
INVALID_USER = "User provided is invalid."
SERVER_ERROR = "An error occured on the server."

# Default Role Names
DEFAULT_ADMIN_ROLE = "ADMIN"
DEFAULT_GENERAL_USER_ROLE = "GENERAL"

# List of permissions General Users should have
GENERAL_USER_PERMISSIONS = [
    models.PermissionsEnum.CAN_POST_DASHBOARD,
    models.PermissionsEnum.CAN_VIEW_DASHBOARD
]

# List of permissions Admin should have
ADMIN_PERMISSION_LIST = [
    models.PermissionsEnum.CAN_ACCESS_ADMIN,
    models.PermissionsEnum.CAN_UPDATE_ADMIN,
    models.PermissionsEnum.CAN_INSERT_ADMIN,
    models.PermissionsEnum.CAN_POST_DASHBOARD,
    models.PermissionsEnum.CAN_VIEW_DASHBOARD
]

# Token
EMAIL_CONFIRMATION_TOKEN = "email-confirm-key"
RESET_PASSWORD_TOKEN = "reset-password-key"
REGISTRATION_TOKEN_MAX_AGE = 24 * 60 * 60  # 24 HOURS
RESET_TOKEN_MAX_AGE = 5 * 60  # 5 MINUTES

BAD_SIGNATURE_TOKEN_ERROR = "Token provided is not valid."
EXPIRED_SIGNATURE_TOKEN_ERROR = "Token has expired."


# Regex Checker
def check_valid_characters(string, regex_pattern):
    """
    Validates Names(Username, Firstname, and Lastname).

    Args:
      name: Plain text name to be validated

    Returns:
      Boolean indicating result of operation.

    Raises:
      TypeError: If invalid parameter type is give, i.e not a string.
    """
    if isinstance(string, str) and isinstance(regex_pattern, str):
        regex = re.compile(regex_pattern)
        return regex.search(string) is not None
    else:
        raise TypeError("Only strings are supported")


# Length Checker
def check_length(string, min_len=0, max_len=1):
    """
    Checks Length of String if matches the minimum and maximum specified.

    Args:
      string: Plain text name to be validated
      max_len: Max value int
      min_len: Min value int

    Returns:
      Boolean indicating result of operation.

    Raises:
      TypeError: If invalid parameter type is give, i.e not a string.
    """
    if isinstance(string, str):
        return min_len <= len(string) <= max_len
    else:
        raise TypeError("Only strings are supported")


# Decorator function for functions validating names
def validate_names(func):
    def inner(user, name):
        # Checks if valid name
        valid_name = check_valid_characters(
            name,
            NAMES_REGEX)

        # Checks if valid length
        valid_len = check_length(
            name,
            min_len=MIN_NAMES,
            max_len=MAX_NAMES)

        if valid_name:
            if valid_len:
                if user and user.active:
                    return func(user, name)
                else:
                    return False, INVALID_USER
            else:
                return False, INVALID_FIELD_LENGTH(
                    MIN_NAMES, MAX_NAMES)
        else:
            return False, NAME_REQUIREMENTS
    return inner


# Decorator function for functions validating passwords
def validate_password(func):
    def inner(user, password):
        valid_pwd = check_valid_characters(
            password,
            PASSWORD_REGEX)
        valid_len = check_length(
            password,
            MIN_PASSWORD,
            MAX_PASSWORD)

        if valid_pwd:
            if valid_len:
                if user and user.active:
                    return func(user, password)
                else:
                    return False, INVALID_USER
            else:
                return False, INVALID_FIELD_LENGTH(
                    MIN_PASSWORD, MAX_PASSWORD)
        else:
            return False, PASSWORD_REQUIREMENTS
    return inner


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
    except SignatureExpired:
        return None, EXPIRED_SIGNATURE_TOKEN_ERROR
    except BadSignature:
        return None, BAD_SIGNATURE_TOKEN_ERROR
    except Exception as e:
        print("An error occured while confirming token: {}".format(e))
        return None, SERVER_ERROR

    user = models.User.query.filter_by(email=email).first()
    if user:
        return user, ""
    else:
        return None, SERVER_ERROR


def activate_user(user):
    """
    Activates user if not already activated.

    Args:
      user: User object.

    Returns:
      Boolean indicating if user was activated.
    """
    if not user.active:
        status = user.activate_user()
        if status:
            return status, ""
        else:
            return False, SERVER_ERROR
    else:
        return False, USER_ALREADY_ACTIVE


@validate_names
def change_username(user, new_username):
    """
    Changes Username.

    Args:
      user: User object.
      new_username: New username for client.

    Returns:
      Boolean indicating if email was changed.
    """
    status = user.change_username(new_username)
    return status, ""


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
    return status, ""


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
    return status, ""


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
            return status, ""
        else:
            return False, INVALID_USER
    except EmailNotValidError as e:
        return False, e


@validate_password
def change_user_password(user, new_password):
    """
    Changes User password.

    Args:
      user: User object.
      password: Plain text password of new password

    Returns:
      Boolean indicating if password was changed.
    """
    status = user.change_password(new_password)
    return status, ""


@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))


def check_username_exists(username):
    """
    Checks if Username exists in User table.

    Args:
      username: username

    Returns:
      Boolean indicating result of operation.
    """
    user_ = models.User()
    user_exists = user_.query.filter_by(
        username=username).first()
    if user_exists:
        return True
    else:
        return False


def check_email_exists(email):
    """
    Checks if Email exists in User table.

    Args:
      username: username

    Returns:
      Boolean indicating result of operation.
    """
    user_ = models.User()
    email_exists = user_.query.filter_by(
        email=email).first()
    if email_exists:
        return True
    else:
        return False


# Click callback used in validating email, password and names
def validate_callback(ctx, param, value):
    if param.name == "username" or param.name == "first_name" or param.name == "last_name":
        # Checks if valid name
        valid_name = check_valid_characters(value, NAMES_REGEX)

        # Checks if valid length
        valid_len = check_length(value, min_len=MIN_NAMES, max_len=MAX_NAMES)

        if valid_name:
            if valid_len:
                return value
            else:
                raise click.BadParameter(
                    INVALID_FIELD_LENGTH(
                        MIN_NAMES, MAX_NAMES))
        else:
            raise click.BadParameter(
                NAME_REQUIREMENTS)
    elif param.name == "email":
        try:
            # Attempts to validate if proper email, raises Exception if not
            validate_email(value)
            return value
        except EmailNotValidError as e:
            raise click.BadParameter(e)

    elif param.name == "password":
        valid_pwd = check_valid_characters(value, PASSWORD_REGEX)
        valid_len = check_length(value, MIN_PASSWORD, MAX_PASSWORD)

        if valid_pwd:
            if valid_len:
                return value
            else:
                raise click.BadParameter(
                    INVALID_FIELD_LENGTH(
                        MIN_PASSWORD, MAX_PASSWORD))
        else:
            click.echo(PASSWORD_REQUIREMENTS)
            raise click.BadParameter(PASSWORD_REQUIREMENTS)
    else:
        return value


def get_Role(role_name):
    """
    Gets Role object using role_name passed.

    Args:
      role_name: Name for Role.

    Returns:
      Role object if any.
    """
    user_role = models.Role().query.filter_by(name=role_name).first()
    return user_role


def get_Permission(role):
    """
    Get Permission object(s).

    Args:
      role: Role object.

    Returns:
      Permission object if any.
    """
    role_permissions = models.Permissions().query.filter_by(
        role_id=role.id).first()

    return role_permissions


def add_Role(role_name):
    """
    Creates Role object and adds it to Session if no error occurs.

    Args:
      role_name: Name for Role

    Returns:
      Boolean indicating result of operation.
    """
    try:
        user_role = models.Role(name=role_name)
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
        user_ = models.User()
        user_created = user_.add_user(user_details)
        return user_created
    except Exception as e:
        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
        return False


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
    if role_permissions is None:
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
        print("An error occured while committing: {}".format(e))
        # Rollback session
        db.session.rollback()
        return False

    # Appends User Role to user details Dict
    user_details["user_role"] = user_role.id

    # Create Admin User
    user_created = add_User(user_details)
    if user_created:
        print("User: {} has been successfully added".format(
            user_details["username"]))

        return True
    else:
        return False


def authenticate_user(username, password):
    """
    Authenticates User account given username, and password.

    Args:
      username: Username.
      password: Password in plaintext.

    Returns:
      Boolean indicating result of operation.
    """
    user_ = models.User().query.filter_by(
        username=username).first()
    if user_:
        user_authenticated = user_.check_hash(password)
        if user_authenticated:
            return user_
        else:
            return None
    else:
        return None


@auth_bp.cli.command('createsuperuser')
@click.option(
    '--username',
    prompt="Enter Username?",
    default="admin_" + os.urandom(2).hex(),
    callback=validate_callback,
    help="Username for account")
@click.option(
    '--first_name',
    prompt="Enter Firstname?",
    callback=validate_callback,
    help="Firstname of user")
@click.option(
    '--last_name',
    prompt="Enter Lastname?",
    callback=validate_callback,
    help="Lastname of user")
@click.option(
    '--email',
    prompt="Enter Email?",
    callback=validate_callback,
    help="Email address to send activation url to")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    callback=validate_callback,
    help="User password for user with administrative role")
def createsuperuser(username, first_name, last_name, email, password):
    """
    Creates Admin User with appropriate Role and Permission.
    Intended to be used when initializing the web application.

    Args:
      username: Username to be displayed on website.
      first_name: First name of user.
      last_name: Last name of user.
      email: Email of user for verification and recovery.
      password: Plain text password to be used by user.
    """
    # Admin User details
    admin_details = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "active": True  # Admin user have account activated by default
    }

    admin_created = account_creation(
        user_details=admin_details,
        role_name=DEFAULT_ADMIN_ROLE,
        permissions=ADMIN_PERMISSION_LIST)
    return admin_created
