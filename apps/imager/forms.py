from flask_wtf import FlaskForm
from flask_wtf.file import (
    FileField,
    FileAllowed,
    FileRequired)

from wtforms.validators import (
    InputRequired,
    Length)
from wtforms.fields import (
    StringField,
    SubmitField)


class UploadFileForm(FlaskForm):
    name = StringField(
        'Title',
        validators=[
            InputRequired(),
            Length(
                min=1,
                max=100,
                message="Name must be between 1 and 20 characters.")
        ])
    file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(
                ["jpg", "png", "jpeg"],
                message='Images only!')])
    submit = SubmitField("Submit")
