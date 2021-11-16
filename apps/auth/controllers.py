import os
import re
import click
from .. import db
from . import models
from . import auth_bp

from email_validator import validate_email, EmailNotValidError


# Min and Max length of First and Last names
MIN_NAMES = 2
MAX_NAMES = 20

# Min and Max length of password
MIN_PASSWORD = 8
MAX_PASSWORD = 128

"""
Regex patterns constants
"""
# Only single words consisting of numbers, letters, undercore(s) or hyphens
NAMES_REGEX = "^[a-zA-Z0-9-_]+$"

# Password regex:
# At least one upper case English letter, (?=.*?[A-Z])
# At least one lower case English letter, (?=.*?[a-z])
# At least one digit, (?=.*?[0-9])
# At least one special character, (?=.*?[#?!@$%^&*-])
PASSWORD_REGEX = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{4,}$$"


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
                    '{} must be between {} and {} characters. Please try again.'.format(
                        param.name.title(), MIN_NAMES, MAX_NAMES))
        else:
            raise click.BadParameter(
                f'{param.name.title()} must contain letters, numbers, and underscores only. Please try again.')
    elif param.name == "email":
        try:
            valid = validate_email(value)
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
                    'Password must be between {} \
                    and {} characters. Please try again.'.format(
                        MIN_PASSWORD, MAX_PASSWORD))
        else:
            password_requirements = "\nPassword has to have:\n\
    > At least one upper case English letter,\n\
    > At least one lower case English letter,\n\
    > At least one digit,\n\
    > At least one special character,\n"
            click.echo(password_requirements)
            raise click.BadParameter(password_requirements)
    else:
        return value


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
        return True

    except Exception as e:
        # Rollback session
        db.session.rollback()

        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
        return False


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
        return True
    except Exception as e:
        # Rollback session
        db.session.rollback()

        # Logs exceptions
        print("Exception occured when creating Role: {}".format(e))
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
    # Create Admin Role if none exists
    admin_role = models.Role().query.filter_by(name='admin').first()
    if admin_role is None:
        role_created = add_Role(admin_role)
        if not role_created:
            return

    # List of permissions Admin should have
    admin_permissions_list = [
        models.PermissionsEnum.CAN_ACCESS_ADMIN,
        models.PermissionsEnum.CAN_UPDATE_ADMIN,
        models.PermissionsEnum.CAN_INSERT_ADMIN,
        models.PermissionsEnum.CAN_POST_DASHBOARD,
        models.PermissionsEnum.CAN_VIEW_DASHBOARD
    ]

    # Add Admin Permissions to Admin Role if none exists
    admin_permissions = models.Permissions().query.filter_by(
        role_id=admin_role.id).all()
    if admin_permissions is None:
        for permission in admin_permissions_list:
            permission_created = add_Permission(
                role_id=admin_role.id,
                permission_index=permission.value)

            if not permission_created:
                return

    # Commit Admin Roles and Permissions added
    try:
        # Commit session
        db.session.commit()
    except Exception as e:
        print("An error occured while committing: {}".format(e))
        # Rollback session
        db.session.rollback()
        return

    # Admin User details
    auth_dict = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "user_role": admin_role.id,
        "password": password
    }

    # Create Admin User
    admin_user = models.User()
    user_created = admin_user.add_user(auth_dict)
    if user_created:
        print("User: {} has been successfully added".format(
            admin_user.username))
