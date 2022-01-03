import os
import click
from .utils import *
from .auth import *
from . import auth_bp
from .controllers import account_creation
from email_validator import validate_email, EmailNotValidError


# Click callback used in validating email, password and names
def validate_callback(ctx, param, value):
    if param.name == "username" or param.name == "first_name" \
            or param.name == "last_name":
        # Checks if valid name
        valid_name = check_valid_characters(
            value,
            NAMES_REGEX)

        # Checks if valid length
        valid_len = check_length(
            value,
            min_len=MIN_NAMES,
            max_len=MAX_NAMES)

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
        valid_pwd = check_valid_characters(
            value, PASSWORD_REGEX)
        valid_len = check_length(
            value, MIN_PASSWORD, MAX_PASSWORD)

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
        "email_confirmed": True  # Admin user have account activated by default
    }

    admin_created = account_creation(
        user_details=admin_details,
        role_name=DEFAULT_ADMIN_ROLE,
        permissions=ADMIN_PERMISSION_LIST)
    return admin_created
