import os
import re
import click
from .. import db
from . import models
from . import auth_bp

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


# Click callback used in validating email, password and names
def validate_callback(ctx, param, value):
    if param.name == "username" or param.name == "first_name" or param.name == "last_name":
        valid_name = check_valid_characters(value, NAMES_REGEX)
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
        admin_user = models.User()
        user_created = admin_user.add_user(user_details)
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
      Exception: Any exeption that occurs when commiting User, Role and Permissions.
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

    # Commit General Roles and Permissions added
    try:
        # Commit session
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
        "password": password
    }

    admin_created = account_creation(
        user_details=admin_details,
        role_name=DEFAULT_ADMIN_ROLE,
        permissions=ADMIN_PERMISSION_LIST)
    return admin_created
