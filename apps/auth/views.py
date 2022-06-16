from flask import (
    request,
    redirect,
    render_template,
    flash,
    current_app,
    url_for)
from flask_login import (
    current_user,
    login_user,
    logout_user,
    login_required)
from werkzeug.urls import url_parse

from . import auth_bp

from .utils import *
from .forms import *
from .controllers import *
from .create_admin import *


# Registration
@auth_bp.route("/registration", methods=["GET", "POST"])
def registration():
    if current_user.is_anonymous:
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
                flash(
                    USERNAME_ALREADY_EXISTS(request.form["username"]),
                    "error")

            # Check if Email has been used by other accounts
            email_exists = check_email_exists(
                request.form["email"])
            if email_exists:
                flash(
                    EMAIL_ALREADY_USED(request.form["email"]),
                    "error")

            # Creates account
            if not username_exists and not email_exists:
                user_created = account_creation(
                    user_details=user_details,
                    role_name=DEFAULT_GENERAL_USER_ROLE,
                    permissions=GENERAL_USER_PERMISSIONS)
                if user_created:
                    try:
                        if "MAIL_SERVER" in current_app.config and \
                            "MAIL_PORT" in current_app.config and \
                            "MAIL_USERNAME" in current_app.config and \
                            "MAIL_PASSWORD" in current_app.config:
                            # Send token via EMAIL
                            token = generate_token(
                                request.form["email"],
                                EMAIL_CONFIRMATION_TOKEN)

                            subject = EMAIL_SUBJECT
                            body = render_template(
                                "auth/email_confirmation.html",
                                username=user_details["username"],
                                activation_link=url_for(
                                    "auth.activate_account",
                                    activation_token=token,
                                    _external=True))

                            sender = current_app.config['MAIL_USERNAME']
                            recipients = [current_app.config[
                                "TEST_EMAIL_CONFIG"]] or [request.form["email"]]
                            
                            # TODO: Add config to disable this for testing.
                            send_email(subject, body, sender, recipients)
                            
                            flash(USER_CREATED, "success")
                        else:
                            flash(USER_CREATED_NO_EMAIL, "success")
                    except Exception as e:
                        # TODO: Allow resending confirmation email,
                        # if initial one failed.
                        print("An error occured sending email: ", e)
                        flash(EMAIL_SENDING_FAILED, "error")
                        return redirect(url_for('auth.registration'))

                    return redirect(url_for("auth.login"))
                else:
                    flash(ACCOUNT_CREATION_ERROR, "error")
                    return redirect(url_for('auth.registration'))

        return render_template(
            'auth/registration.html',
            form=registration_form)
    else:
        flash(USERNAME_ALREADY_LOGGED_IN(current_user.username), "info")
        return redirect(url_for("imager.index"))


# Activate account
@auth_bp.route("/activate")
def activate_account():
    activation_token = request.args.get("activation_token")
    if activation_token:
        user, error_status = validate_token(
            activation_token,
            EMAIL_CONFIRMATION_TOKEN,
            REGISTRATION_TOKEN_MAX_AGE)
        if user:
            user_activated, error_status = confirm_email(user)
            if user_activated:
                flash(EMAIL_CONFIRMED(user.username), "success")

                # Logs user in
                login_user(user)
            else:
                if error_status == "email-confirmed":
                    flash(EMAIL_ALREADY_CONFIRMED, "error")
                elif error_status == "server-error":
                    flash(SERVER_ERROR, "error")
                else:
                    flash(SERVER_ERROR, "error")
        else:
            if error_status == "expired-token":
                flash(EXPIRED_SIGNATURE_TOKEN_ERROR, "error")
            elif error_status == "bad-token":
                flash(BAD_SIGNATURE_TOKEN_ERROR, "error")
            elif error_status == "server-error":
                flash(SERVER_ERROR, "error")
            else:
                flash(SERVER_ERROR, "error")
            return redirect(url_for('imager.index'))
        return redirect(url_for('imager.index'))
    else:
        flash(NO_ACTIVATION_TOKEN_PASSED, "error")
        return redirect(url_for('imager.index'))


# Forgot Password
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    forgot_password = ForgotPassword()
    if forgot_password.validate_on_submit():
        email_exists = check_email_exists(
            request.form["email"])
        if email_exists:
            if "MAIL_SERVER" in current_app.config and \
                "MAIL_PORT" in current_app.config and \
                "MAIL_USERNAME" in current_app.config and \
                "MAIL_PASSWORD" in current_app.config:
                # Send an email to reset password.
                reset_token = generate_token(
                    request.form["email"],
                    RESET_PASSWORD_TOKEN)

                subject = 'Imager Reset password'
                body = render_template(
                    "auth/email_forgot_password.html",
                    reset_link=url_for(
                        "auth.reset_password",
                        reset_token=reset_token,
                        _external=True))
                sender = current_app.config['MAIL_USERNAME']

                recipients = [
                    current_app.config["TEST_EMAIL_CONFIG"]] or [
                    request.form["email"]]
                
                send_email(subject, body, sender, recipients)
                flash(RESET_LINK_SENT, "success")
            else:
                flash(RESET_LINK_SENT_NO_EMAIL, "success")
        else:
            flash(NO_EMAIL_FOUND, "error")
    return render_template(
        'auth/forgotpassword.html',
        form=forgot_password)


# Reset Password
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "GET":
        reset_token = request.args.get("reset_token")
        if not reset_token:
            flash(NO_TOKEN_PROVIDED, "error")
            return redirect(url_for("imager.index"))

    reset_password = ResetPassword()
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
                flash(SUCCESS_PWD_CHANGE, "success")
                return redirect(url_for("auth.login"))
            else:
                flash(ERROR_PWD_CHANGE, "error")
                return redirect(url_for("auth.forgot_password"))
        else:
            if message_status == "bad-token":
                flash(BAD_SIGNATURE_TOKEN_ERROR, "error")
            elif message_status == "expired-token":
                flash(EXPIRED_SIGNATURE_TOKEN_ERROR, "error")
            elif message_status == "server-error":
                flash(SERVER_ERROR, "error")
            else:
                flash(SERVER_ERROR, "error")
            return redirect(url_for("auth.forgot_password"))

    return render_template(
        'auth/resetpassword.html',
        form=reset_password,
        token=reset_token)


# Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_anonymous:
        login_form = LoginForm()

        next_page = request.args.get('next', url_for('imager.index'))

        if login_form.validate_on_submit():
            user_authenticated = authenticate_user(
                request.form["username_email"],
                request.form["password"])
            if user_authenticated:
                if user_authenticated.email_confirmed \
                        and user_authenticated.active:
                    # Logs user in
                    login_user(user_authenticated)

                    # Redirect Page
                    next_page = request.form["next"]

                    if not next_page or url_parse(next_page).netloc != '':
                        next_page = url_for('imager.index')
                    return redirect(next_page)
                elif not user_authenticated.active:
                    flash(ACCOUNT_DEACTIVATED, "info")
                else:
                    flash(CONFIRM_EMAIL, "info")
            else:
                flash(INVALID_USERNAME_PASSWORD, "error")

        return render_template(
            'auth/login.html',
            next_page=next_page,
            form=login_form)
    else:
        flash(USERNAME_ALREADY_LOGGED_IN(current_user.username), "info")
        return redirect(url_for("imager.index"))


# Logout
@auth_bp.route("/logout")
@login_required
def logout():
    # Logs user out.
    logout_user()
    return redirect(url_for("imager.index"))
