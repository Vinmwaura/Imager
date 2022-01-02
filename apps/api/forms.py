from flask_wtf import FlaskForm
from wtforms.validators import (
    InputRequired,
    Length)
from wtforms.fields import (
    StringField,
    SubmitField,
    SelectField)
from .utils import *


class AddClientForm(FlaskForm):
    client_name = StringField(
        "Client Name:",
        validators=[
            InputRequired(),
            Length(
                min=MIN_NAMES,
                max=MAX_NAMES,
                message=INVALID_FIELD_LENGTH(MIN_NAMES, MAX_NAMES)
            )
        ]
    )
    redirect_uris = StringField(
        "Redirection URI:",
        validators=[])
    token_endpoint_auth_method = SelectField(
        'Token Endpoint Auth Method',
        choices=[
            ('client_secret_basic', 'client_secret_basic'),
            ('client_secret_post', 'client_secret_post'),
            ('none', 'none')])
    submit = SubmitField('Submit')
