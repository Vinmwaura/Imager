import os
import re
import click
from .. import db
from . import models
from . import auth_bp


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
        At least one upper case English letter, (?=.*?[A-Z])
        At least one lower case English letter, (?=.*?[a-z])
        At least one digit, (?=.*?[0-9])
        At least one special character, (?=.*?[#?!@$%^&*-])
        Minimum 8, Maximum 128 in length.{8, 128} (with the anchors)
    """
    password_regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,128}$$"
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
        password_requirements = "\nPassword has to be:\n\
    > At least one upper case English letter,\n\
    > At least one lower case English letter,\n\
    > At least one digit,\n\
    > At least one special character,\n\
    > Minimum 8, Maximum 128 in length.\n"
        valid_pwd = validate_password(value)
        if valid_pwd:
            return value
        else:
            click.echo(password_requirements)
            raise click.BadParameter("Invalid password, please try again.")
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
    # Create Admin Role if none exists
    admin_role = models.Role().query.filter_by(name='admin').first()
    if admin_role is None:
        try:
            admin_role = models.Role(name='admin')
            db.session.add(admin_role)

            # Commit session
            db.session.commit()
        except Exception as e:
            # Rollback session
            db.session.rollback()
            raise e

    # Add Admin Permissions to Admin Role
    permission_list = [
        models.PermissionsEnum.CAN_ACCESS_ADMIN,
        models.PermissionsEnum.CAN_UPDATE_ADMIN,
        models.PermissionsEnum.CAN_INSERT_ADMIN,
        models.PermissionsEnum.CAN_POST_DASHBOARD,
        models.PermissionsEnum.CAN_VIEW_DASHBOARD
    ]
    admin_permissions = models.Permissions().query.filter_by(
        role_id=admin_role.id).first()
    if admin_permissions is None:
        try:
            for permission_val in permission_list:
                admin_permissions = models.Permissions(
                    role_id=admin_role.id,
                    permission=permission_val.value)
                db.session.add(admin_permissions)

            # Commit session
            db.session.commit()
        except Exception as e:
            print("Error: ", e)
            # Rollback session
            db.session.rollback()
            raise e

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
    admin_user.add_user(auth_dict)

    print("User: {} has been successfully added".format(admin_user.username))
