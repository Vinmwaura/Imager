from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, DataRequired
from wtforms.fields import (
    SelectMultipleField,
    StringField,
    SubmitField,
    SelectField)


class AddClientForm(FlaskForm):
    application_name = StringField(
        "Application Name:",
        validators=[InputRequired()])
    # scope = StringField(
    #    "Scope:",
    #    validators=[InputRequired()])
    redirect_uris = StringField(
        "Redirection URI:",
        validators=[])
    grant_types = SelectMultipleField(
        choices=[
            ('refresh_token', 'Refresh Token'),
            ('authorization_code', 'Authorization Code'),
            ('password', 'Password'),
            ('client_credentials', 'Client Credentials')],
        validators=[InputRequired()])
    token_endpoint_auth_method = SelectField(
        'Token Endpoint Auth Method',
        choices=[
            ('client_secret_basic', 'client_secret_basic'),
            ('client_secret_post', 'client_secret_post'),
            ('none', 'none')])
    submit = SubmitField('Submit')
