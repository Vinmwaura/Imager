from . import auth_bp
from flask import request, render_template, flash
from flask_login import current_user, login_user, logout_user
# from http import HTTPStatus

from .forms import *
from .controllers import (
    load_user,
    account_creation,
    authenticate_user,
    check_username_exists,
    check_email_exists,
    DEFAULT_GENERAL_USER_ROLE,
    GENERAL_USER_PERMISSIONS,
    USERNAME_ALREADY_EXISTS,
    EMAIL_ALREADY_USED)


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

        # Check if username has been created
        username_exists = check_username_exists(
            request.form["username"])
        if username_exists:
            flash(USERNAME_ALREADY_EXISTS(request.form["username"]))

        # Check if Email has been used by other accounts
        email_exists = check_email_exists(
            request.form["email"])
        if email_exists:
            flash(EMAIL_ALREADY_USED(request.form["email"]))

        # Creates account
        user_created = account_creation(
            user_details=user_details,
            role_name=DEFAULT_GENERAL_USER_ROLE,
            permissions=GENERAL_USER_PERMISSIONS)
        if user_created:
            return "User has been successfully created, Check email"
        else:
            flash("An error occured creating an account, please try again!")
    return render_template(
        'auth/registration.html',
        form=registration_form)


# Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_authenticated = authenticate_user(
            request.form["username"],
            request.form["password"])
        if user_authenticated:
            login_user(user_authenticated)
            return "User {} logged in.".format(current_user.username)
        else:
            flash("Invalid Username or password")
    return render_template(
        'auth/login.html',
        form=login_form)


# Logout
@auth_bp.route("/logout")
def logout():
    logout_user()
    return "Logged out, redirecting to homepage..."


# Activate account
@auth_bp.route("/activate")
def activate_account():
    activation_token = request.args.get("activation_token")
    if activation_token:
        pass
    else:
        pass
