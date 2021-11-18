from . import auth_bp
from flask import (
    request,
    render_template,
    flash,
    current_app,
    abort)
from flask_login import current_user, login_user, logout_user
# from http import HTTPStatus

from .forms import *
from .controllers import (
    activate_user,
    load_user,
    account_creation,
    authenticate_user,
    check_username_exists,
    check_email_exists,
    generate_token,
    validate_token,
    DEFAULT_GENERAL_USER_ROLE,
    GENERAL_USER_PERMISSIONS,
    USERNAME_ALREADY_EXISTS,
    EMAIL_ALREADY_USED,
    EMAIL_CONFIRMATION_TOKEN)


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
            # Send token via EMAIL
            token = generate_token(
                request.form["email"],
                EMAIL_CONFIRMATION_TOKEN)
            print(token)
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
        user = validate_token(activation_token, EMAIL_CONFIRMATION_TOKEN)
        if user:
            user_activated = activate_user(user)
            if user_activated is not None and not user.active:
                return "User {} has been activated".format(user.username)
            elif user_activated is not None and user.active:
                return "Email has already been confirmed."
            else:
                return "An error occured, please try again."
        else:
            abort(404)
    else:
        return "No activation token received"
