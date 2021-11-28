import os
import uuid

from flask import current_app
from flask_login import current_user

from .. import db
from . import models  # Imager Models

from .utils import *


def get_user_content(user):
    user_content = models.UserContent().query.filter_by(
        user_id=user.id).first()
    return user_content


def create_user_content(user, directory_name):
    user_content = models.UserContent(
        user_id=user.id,
        content_location=directory_name)

    db.session.add(user_content)

    try:
        db.session.commit()
        return True
    except Exception as e:
        print("An error occured while commiting UserContent: ", e)
        db.session.rollback()
        return False


def create_or_get_user_content(user):
    user_content = get_user_content(user)
    if user_content:
        return user_content

    file_path = current_app.config["UPLOAD_PATH"]
    directory_created, directory_name = create_content_directory(file_path)
    if directory_created:
        user_content_created = create_user_content(
            user,
            directory_name)
        if user_content_created:
            return get_user_content(user)
        return None
    else:
        return None


def save_user_image(user, file, image_details):
    user_content = get_user_content(user)
    if not user_content:
        return False

    image_details["user_content_id"] = user_content.id

    file_ext = os.path.splitext(file.filename)[1]
    filename = generate_filename(
        user.id,
        file_ext)
    image_details["file_location"] = filename

    image_content = models.ImageContent(**image_details)

    db.session.add(image_content)
    try:
        # Saves file using user location and new filename
        file.save(
            os.path.join(*[
                current_app.config["UPLOAD_PATH"],
                user_content.content_location,
                filename
            ])
        )

        # Commits ImageContent with filename
        db.session.commit()

        return True
    except Exception as e:
        print("An error occured while commiting ImageContent: ", e)

        db.session.rollback()

        # Removes file if an error occured and file was saved
        try:
            os.remove(
                os.path.join(*[
                    current_app.config["UPLOAD_PATH"],
                    user_content.content_location,
                    filename
                ]))
        except Exception as e:
            print("An exception occured while removing file: ", e)

        return False
