from flask_wtf import FlaskForm
from wtforms.validators import (
    Email,
    EqualTo,
    Regexp,
    InputRequired,
    Length
)
from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
    EmailField
)
from .controllers import (
    PASSWORD_REGEX,
    NAMES_REGEX,
    MIN_NAMES,
    MAX_NAMES,
    MIN_PASSWORD,
    MAX_PASSWORD,
    NAME_REQUIREMENTS,
    PASSWORD_REQUIREMENTS,
    INVALID_FIELD_LENGTH,
)


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            InputRequired(),
            Regexp(NAMES_REGEX, message=NAME_REQUIREMENTS),
            Length(
                min=MIN_NAMES,
                max=MAX_NAMES,
                message=INVALID_FIELD_LENGTH(MIN_NAMES, MAX_NAMES))
        ])
    first_name = StringField(
        'First Name',
        validators=[
            InputRequired(),
            Regexp(NAMES_REGEX, message=NAME_REQUIREMENTS),
            Length(
                min=MIN_NAMES,
                max=MAX_NAMES,
                message=INVALID_FIELD_LENGTH(MIN_NAMES, MAX_NAMES))
        ])
    last_name = StringField(
        'Last Name',
        validators=[
            InputRequired(),
            Regexp(NAMES_REGEX, message=NAME_REQUIREMENTS),
            Length(
                min=MIN_NAMES,
                max=MAX_NAMES,
                message=INVALID_FIELD_LENGTH(MIN_NAMES, MAX_NAMES))
        ])
    email = EmailField(
        'Email',
        validators=[
            InputRequired(),
            Email()])
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            Regexp(PASSWORD_REGEX, message=PASSWORD_REQUIREMENTS.replace("\n", "").replace(">", "")),
            EqualTo('password_confirmation', 'Passwords must match'),
            Length(
                min=MIN_PASSWORD,
                max=MAX_PASSWORD,
                message=INVALID_FIELD_LENGTH(MIN_PASSWORD, MAX_PASSWORD))
        ])
    password_confirmation = PasswordField('Confirm Password')
    submit = SubmitField('Register')
