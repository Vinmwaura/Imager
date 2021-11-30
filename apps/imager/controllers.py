import os

from flask import current_app

from .. import db
from . import models  # Imager Models
from .. import auth

from .utils import *
from PIL import Image, ImageOps


PER_PAGE = 20
ERROR_OUT = True
MAX_PER_PAGE = 100
THUMBNAIL_SIZE = (240, 240)


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

    file_path = current_app.config["UPLOAD_PATH"]

    # Check if folder based on db record exists, and if not creates it
    is_dir = os.path.isdir(
        os.path.join(
            file_path,
            user_content.content_location))
    if not is_dir:
        directory_created, _ = create_content_directory(
            file_path,
            user_content.content_location)
        if directory_created:
            """
            # Deletes old non-existant Imagecontent from db
            image_contents = models.ImageContent().query.filter_by(
                user_content_id=user_content.id)
            image_contents.delete()
            """
            pass

    # Adds User content id to Image Content.
    image_details["user_content_id"] = user_content.id

    # Generates unique filename for uploaded image.
    filename = generate_filename()
    image_details["file_id"] = filename

    # Creates Image Content for storing in database
    image_content = models.ImageContent(**image_details)

    db.session.add(image_content)

    file_ext = os.path.splitext(file.filename)[1]

    image_path = os.path.join(*[
        file_path,
        user_content.content_location,
        filename + file_ext
    ])

    thumbnail_path = os.path.join(*[
        file_path,
        user_content.content_location,
        'thumbnails',
        filename + file_ext
    ])
    try:
        # Saves file using user location and new filename
        file.save(image_path)

        # Create Thumbnails using saved images
        original_image = Image.open(image_path)
        thumbnail_image = ImageOps.fit(
            image=original_image,
            size=THUMBNAIL_SIZE,
            method=3,
            bleed=0.0,
            centering=(0.5, 0.5))

        # Save thumbnail to Thumbnail directory.
        thumbnail_image.save(thumbnail_path)

        # Commits ImageContent with filename
        db.session.commit()

        return True
    except Exception as e:
        print("An error occured while saving user image: ", e)

        db.session.rollback()

        # Removes file if an error occured and file was saved
        try:
            os.remove(image_path)
            os.remove(thumbnail_path)
        except Exception as e:
            print("An exception occured while removing files: ", e)

        return False


def image_pagination(obj, page=1):
    image_pagination = obj.paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=ERROR_OUT,
        max_per_page=MAX_PER_PAGE)
    return image_pagination.items


def load_images_by_time():
    image_content = models.ImageContent.query.order_by(
        models.ImageContent.upload_time.desc())
    return image_content


def load_images_by_user(username):
    user = auth.models.User().query.filter_by(username=username).first()
    if not user:
        return None, None

    user_content = models.UserContent().query.filter_by(
        user_id=user.id).first()
    if not user_content:
        return user, None

    image_content = models.ImageContent().query.filter_by(
        user_content_id=user_content.id)
    return user, image_content


def load_images_by_tags(tags):
    pass


def load_image_by_id(image_id):
    image_content = models.ImageContent().query.filter_by(
        file_id=image_id).first()
    return image_content
