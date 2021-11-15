import os
import re
import click
# from . import models
from . import auth_bp

"""
@auth_bp.cli.command('createsuperuser')
@click.option('--username', prompt="Enter Username?", help="Username")
@click.option('--firstname', prompt="Enter First Name?", help="Firstname")
@click.option('--lastname', prompt="Enter Lastname?", help="Lastname")
@click.option('--email', prompt="Enter Email?", help="Email address")
def create_super_user(username, firstname, lastname, email):
    click.echo(f"Username: {username}\nFirstname: {firstname}\nLastname: {lastname}\nEmail: {email}")
"""


# Validates firstname, lastname, and username
def validate_names(name):
    """
    Name has to be 4-20 character long,
    no _ or . in the beginning,
    no __ or _. or ._ or .. inside,
    and no _ or . at the end
    """
    name_regex = "^(?=[a-zA-Z0-9._]{4,20}$)(?!.*[_.]{2})[^_.].*[^_.]$"
    if re.search(name_regex, name):
        return True
    else:
        return False


# Validates email
def validate_email(email):
    email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(email_regex, email):
        return True
    else:
        return False


# Validates password
def validate_password(password):
    """
    Password has to be:
        Minimum eight and maximum 10 characters,
        at least one uppercase letter,
        one lowercase letter,
        one number and one special character
    """
    password_regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,128}$"
    if re.search(password_regex, password):
        return True
    else:
        return False


# Click callback
def validate_callback(ctx, param, value):
    if param.name == "username" or param.name == "firstname" or param.name == "lastname":
        valid_name = validate_names(value)
        if valid_name:
            return value
        else:
            raise click.BadParameter('Invalid name, please try again.')
    elif param.name == "email":
        valid_email = validate_email(value)
        if valid_email:
            return value
        else:
            raise click.BadParameter('Invalid email, please try again.')
    elif param.name == "password":
        password_requirements = """
        Password has to be:
        Minimum 8 and maximum 128 characters,
        at least one uppercase letter,
        one lowercase letter,
        one number and one special character.
        """
        valid_pwd = validate_password(value)
        if valid_pwd:
            return value
        else:
            # Hack to get password requirements to print to screen
            click.echo(password_requirements)
            raise click.BadParameter(0)
    else:
        return value


@auth_bp.cli.command('createsuperuser')
@click.option(
    '--username',
    prompt="Enter Username?",
    default="admin",
    callback=validate_callback,
    help="Username for account")
@click.option(
    '--firstname',
    prompt="Enter First Name?",
    default="admin",
    callback=validate_callback,
    help="Firstname of user")
@click.option(
    '--lastname',
    prompt="Enter Lastname?",
    default="admin",
    callback=validate_callback,
    help="Lastname of user")
@click.option(
    '--email',
    prompt="Enter Email?",
    default="admin@gmail.com",
    callback=validate_callback,
    help="Email address to send activation url to")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    callback=validate_callback,
    help="User password for admin")
def createsuperuser(username, firstname, lastname, email, password):
    pass