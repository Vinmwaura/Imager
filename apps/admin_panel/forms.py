from flask_wtf import FlaskForm
from wtforms.fields import (
    SubmitField,
    StringField,
    SelectField,
    EmailField)
from wtforms.validators import (
    Regexp,
    InputRequired,
    Length)

from .. import auth


class RoleForm(FlaskForm):
    role_name = StringField(
        'Name',
        validators=[
            InputRequired(),
            Regexp(
                auth.utils.NAMES_REGEX,
                message=auth.utils.NAME_REQUIREMENTS),
            Length(
                min=auth.utils.MIN_NAMES,
                max=auth.utils.MAX_NAMES,
                message=auth.utils.INVALID_FIELD_LENGTH(
                    auth.utils.MIN_NAMES,
                    auth.utils.MAX_NAMES)
            )])
    submit = SubmitField('Submit')


class UserForm(FlaskForm):
    username = StringField('Username')

    first_name = StringField('First Name')
    last_name = StringField('Last Name')
    email = EmailField('Email')
    role = SelectField('Role')
    submit = SubmitField('Submit')
