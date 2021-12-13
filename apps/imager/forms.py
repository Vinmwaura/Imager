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
    title = StringField(
        'Title',
        validators=[
            InputRequired(),
            Length(
                min=1,
                max=20,
                message="Name must be between 1 and 20 characters.")
        ])
    file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(
                ["jpg", "png", "jpeg"],
                message='Image format not supported!')])
    upload = SubmitField("Upload")


class EditImageForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            InputRequired(),
            Length(
                min=1,
                max=20,
                message="Name must be between 1 and 20 characters.")
        ])

    change = SubmitField("Change")


class DeleteForms(FlaskForm):
    delete = SubmitField("Delete")
