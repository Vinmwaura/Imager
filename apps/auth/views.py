from . import auth_bp
from flask import (
    request,
    redirect,
    render_template,
    flash,
    current_app,
    abort,
    url_for)
from flask_login import current_user, login_user, logout_user
# from http import HTTPStatus

from .forms import *
from .controllers import *

from .. import mail
from flask_mail import Message


def send_email(subject, body, sender, recipients):
    try:
        email_content = Message(
            subject=subject,
            html=body,
            sender=sender,
            recipients=recipients)
        mail.send(email_content)
    except Exception as e:
        print("An exception occured when sending email {}".format(e))


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

        # Check if username has been used in database
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
        if not username_exists and not email_exists:
            user_created = account_creation(
                user_details=user_details,
                role_name=DEFAULT_GENERAL_USER_ROLE,
                permissions=GENERAL_USER_PERMISSIONS)
            if user_created:
                try:
                    # Send token via EMAIL
                    token = generate_token(
                        request.form["email"],
                        EMAIL_CONFIRMATION_TOKEN)

                    subject = 'Imager Activate account'
                    body = 'Congratulations {} on setting an account '\
                        'with Imager, to activate your account go '\
                        'to the following <a href="{}">link</a>'.format(
                            user_details["username"],
                            url_for(
                                'auth.activate_account',
                                activation_token=token,
                                _external=True))
                    sender = current_app.config['MAIL_USERNAME']
                    recipients = [request.form["email"]]

                    send_email(subject, body, sender, recipients)
                except Exception as e:
                    print("An error occured sending email: ", e)
                    flash(
                        "An error occured while sending the \
                        activation email!")

                flash(
                    "User has been successfully created, \
                    Check email for activation link")
                return redirect(url_for("auth.login"))
            else:
                flash(
                    "An error occured creating an account, \
                    please try again!")

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
            # Logs user in
            login_user(user_authenticated)

            # TODO: Redirect to homepage here
            flash("Welcome {}".format(current_user.username))
            # return "User {} logged in.".format(current_user.username)
        else:
            flash("Invalid Username or password, please try again.")
    return render_template(
        'auth/login.html',
        form=login_form)


# Logout
@auth_bp.route("/logout")
def logout():
    # Logs user out
    logout_user()

    # TODO: Redirect to homepage here
    return "Logged out, redirecting to homepage..."


# Activate account
@auth_bp.route("/activate")
def activate_account():
    activation_token = request.args.get("activation_token")
    if activation_token:
        user, message_status = validate_token(
            activation_token,
            EMAIL_CONFIRMATION_TOKEN,
            REGISTRATION_TOKEN_MAX_AGE)
        if user:
            user_activated, message_status = activate_user(user)
            if user_activated:
                message_status = "User {} has been activated".format(
                    user.username)

            return render_template(
                "auth/account_activation.html",
                activation_status=message_status)
        else:
            return render_template(
                "auth/account_activation.html",
                activation_status=message_status)
    else:
        return render_template(
            "auth/account_activation.html",
            activation_status="No activation token received")


# Forgot Password
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    forgot_password = ForgotPassword()
    if forgot_password.validate_on_submit():
        email_exists = check_email_exists(
            request.form["email"])
        if email_exists:
            # Send an email to reset password
            reset_token = generate_token(
                request.form["email"],
                RESET_PASSWORD_TOKEN)

            subject = 'Imager Reset password'
            body = '<h1>Reset password</h1><br>'\
                'You recently requested to reset your Imager '\
                'account password.<br>'\
                '<a href="{}">link</a>'.format(
                    url_for(
                        'auth.reset_password',
                        reset_token=reset_token,
                        _external=True))
            sender = current_app.config['MAIL_USERNAME']
            recipients = [request.form["email"]]
            send_email(subject, body, sender, recipients)
            flash("Check email, password reset link has been sent.")
    return render_template(
        'auth/forgotpassword.html',
        form=forgot_password)


# Reset Password
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    reset_password = ResetPassword()

    reset_token = request.args.get("reset_token")

    if reset_password.validate_on_submit():
        reset_token = request.form["reset_token"]
        password = request.form["password"]

        user, message_status = validate_token(
            reset_token,
            RESET_PASSWORD_TOKEN,
            RESET_TOKEN_MAX_AGE)

        if user:
            status = change_user_password(user, password)
            if status:
                flash("Successfully changed password.")
                return redirect(url_for("auth.login"))
            else:
                flash("An error occured while reseting the password")
                return redirect(url_for("auth.forgot_password"))
        else:
            flash(message_status)
            return redirect(url_for("auth.forgot_password"))

    #if reset_token:
    return render_template(
        'auth/resetpassword.html',
        form=reset_password,
        token=reset_token)
    #else:
    #    abort(404)
