import re
from functools import wraps

from .. import mail
from flask_mail import Message

from flask import url_for

"""
Constants
"""
# Min and Max length of First and Last names
MIN_NAMES = 2
MAX_NAMES = 20

# Min and Max length of password
MIN_PASSWORD = 8
MAX_PASSWORD = 128


# Token
EMAIL_CONFIRMATION_TOKEN = "email-confirm-key"
RESET_PASSWORD_TOKEN = "reset-password-key"
REGISTRATION_TOKEN_MAX_AGE = 24 * 60 * 60  # 24 HOURS
RESET_TOKEN_MAX_AGE = 5 * 60  # 5 MINUTES


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


"""
Error Messages
"""
# Field Requirements
INVALID_USERNAME_PASSWORD = "Invalid Username or password, please try again."
INVALID_USER = "User provided is invalid."
SERVER_ERROR = "An error occured on the server."
PASSWORD_REQUIREMENTS = "Password has to have:\n\
    > At least one upper case English letter,\n\
    > At least one lower case English letter,\n\
    > At least one digit,\n\
    > At least one special character."
NAME_REQUIREMENTS = "Field must contain letters, numbers and underscores only."
INVALID_FIELD_LENGTH = lambda field_min, field_max: 'Field must be between "\
    "{} and {} characters.'.format(field_min, field_max)
USERNAME_ALREADY_EXISTS = lambda username: "Username {} "\
    "already exists.".format(username)

# Emails
EMAIL_ALREADY_CONFIRMED = "User has already confirmed their email"
EMAIL_ALREADY_USED = lambda email: "Email {} has been used "\
    "by another account.".format(email)
EMAIL_SENDING_FAILED = "An error occured while sending the activation email!"
NO_EMAIL_FOUND = "No Email found"

# Account Creation
ACCOUNT_CREATION_ERROR = "An error occured creating an account, please try again!"

# Token
NO_TOKEN_PROVIDED = "No token provided"
BAD_SIGNATURE_TOKEN_ERROR = "Token provided is not valid."
EXPIRED_SIGNATURE_TOKEN_ERROR = "Token has expired."
NO_ACTIVATION_TOKEN_PASSED = "No activation token received"

# Password
ERROR_PWD_CHANGE = "An error occured while reseting the password."


"""
Warning/Info Messages
"""
# User
USERNAME_ALREADY_LOGGED_IN = lambda username: "{} is already logged in".format(
    username)
USER_CREATED = "User has been successfully created, \
    An activation link has been sent to your email."
USER_CREATED_NO_EMAIL = "User has been successfully created, Administrator will need to activate your account."

# Email
CONFIRM_EMAIL = "Kindly confirm your email first to login"
EMAIL_CONFIRMED = lambda username: "Email for {} has been confirmed".format(
    username)
RESET_LINK_SENT = "Check email, password reset link has been sent."
RESET_LINK_SENT_NO_EMAIL = "Admin has been contacted, a reset link will be sent to you."

# Account
ACCOUNT_DEACTIVATED = "Your account has been deactivated!"

SUCCESS_PWD_CHANGE = "Successfully changed password."

"""
Email Content
"""
EMAIL_SUBJECT = "Imager Activate account"


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


# Decorator function for functions validating names
def validate_names(func):
    @wraps(func)
    def inner(user, name):
        # Checks if valid name
        valid_name = check_valid_characters(
            name,
            NAMES_REGEX)

        # Checks if valid length
        valid_len = check_length(
            name,
            min_len=MIN_NAMES,
            max_len=MAX_NAMES)

        if valid_name:
            if valid_len:
                if user and user.active:
                    return func(user, name)
                else:
                    return False, INVALID_USER
            else:
                return False, INVALID_FIELD_LENGTH(
                    MIN_NAMES, MAX_NAMES)
        else:
            return False, NAME_REQUIREMENTS
    return inner


# Decorator function for functions validating passwords
def validate_password(func):
    @wraps(func)
    def inner(user, password):
        valid_pwd = check_valid_characters(
            password,
            PASSWORD_REGEX)
        valid_len = check_length(
            password,
            MIN_PASSWORD,
            MAX_PASSWORD)

        if valid_pwd:
            if valid_len:
                if user and user.active:
                    return func(user, password)
                else:
                    return False, INVALID_USER
            else:
                return False, INVALID_FIELD_LENGTH(
                    MIN_PASSWORD, MAX_PASSWORD)
        else:
            return False, PASSWORD_REQUIREMENTS
    return inner


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
