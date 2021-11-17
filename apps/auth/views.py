from . import auth_bp
from flask import request
from flask import render_template
# from http import HTTPStatus
from .forms import *
from .controllers import (
    account_creation,
    DEFAULT_GENERAL_USER_ROLE,
    GENERAL_USER_PERMISSIONS
)


# Registration
@auth_bp.route("/registration", methods=["GET", "POST"])
def registration():
    registration_form = RegistrationForm()
    if registration_form.validate_on_submit():

        user_details = {
            "username": request.form["username"],
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "password": request.form["password"]
        }

        user_created = account_creation(
            user_details=user_details,
            role_name=DEFAULT_GENERAL_USER_ROLE,
            permissions=GENERAL_USER_PERMISSIONS)
        if user_created:
            # Placeholders
            return "Account has been created, Redirecting to homepage..."
        else:
            return "An error occured creating an account, please try again!"
    return render_template(
        'auth/registration.html',
        form=registration_form)


# Login
@auth_bp.route("/login")
def login():
    pass


# Logout
@auth_bp.route("/logout")
def logout():
    pass


# Activate account
@auth_bp.route("/activate")
def activate_account():
    activation_token = request.args.get("activation_token")
    if activation_token:
        pass
    else:
        pass
