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
    SubmitField,
    TextAreaField)

from .utils import *


class UploadFileForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            InputRequired(),
            Length(
                min=MIN_TITLE_LENGTH,
                max=MAX_TITLE_LENGTH,
                message=INVALID_TITLE_LENGTH)
        ])
    file = FileField(
        "File",
        validators=[
            FileRequired(),
            FileAllowed(
                ["jpg", "png", "jpeg"],
                message='Image format not supported!')])

    description = TextAreaField(
        "Description",
        validators=[
            Length(
                max=MAX_DESC_LENGTH,
                message=INVALID_DESC_LENGTH)])
    upload = SubmitField("Upload")


class EditImageForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            InputRequired(),
            Length(
                min=MIN_TITLE_LENGTH,
                max=MAX_TITLE_LENGTH,
                message=INVALID_TITLE_LENGTH)])
    description = TextAreaField(
        "Description",
        validators=[
            Length(
                max=MAX_DESC_LENGTH,
                message=INVALID_DESC_LENGTH)])

    change = SubmitField("Change")


class DeleteForms(FlaskForm):
    delete = SubmitField("Delete")
