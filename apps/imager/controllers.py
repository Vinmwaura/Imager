import os

from flask import current_app
from sqlalchemy.sql import func

from .. import db
from . import models  # Imager Models
from .. import auth
from .utils import *

from PIL import Image, ImageOps

from sqlalchemy import asc, desc, nulls_first, nulls_last


PER_PAGE = 20
ERROR_OUT = True
MAX_PER_PAGE = 100
THUMBNAIL_SIZE = (240, 240)


def get_image_details(user, images):
    """
    Gets details of image including score aggregation.

    Args:
      user: User object.
      images: Paginated images.

    Returns:
      Dict with details of images.
    """
    data_dict = []
    for image in images:
        temp_dict = {}
        temp_dict["uploaded_by"] = image.user_content.user.username
        temp_dict["title"] = image.title
        temp_dict["file_id"] = image.file_id
        temp_dict["description"] = "" if image.description is None else \
            image.description
        temp_dict["voter_count"] = image_metric(image.file_id)
        temp_dict["upload_date"] = image.upload_time.strftime(
            "%Y-%m-%dT%H:%M:%S")

        if user.is_anonymous:
            temp_dict["personal_vote"] = None
        else:
            vote_counter = models.VoteCounter().query.filter_by(
                user_id=current_user.id,
                image_file_id=image.file_id).first()
            if vote_counter:
                temp_dict["personal_vote"] = vote_counter.vote
            else:
                temp_dict["personal_vote"] = None

        data_dict.append(temp_dict)
    return data_dict


def update_gallery(image_content, new_data):
    try:
        if 'title' in new_data:
            image_content.title = new_data['title']

        if 'description' in new_data:
            image_content.description = new_data['description']

        # Commit Session
        db.session.commit()
        return True
    except Exception as e:
        # Rollback session
        db.session.rollback()

        print("An error occured while commiting ImageContent: ", e)
        return False


def get_user_content(user):
    """
    Gets details for user contents.

    Args:
      user: User object with user's details i.e user id.

    Returns:
      User content object.
    """
    user_content = models.UserContent().query.filter_by(
        user_id=user.id).first()
    return user_content


def get_image_contents_by_time(sort_order="asc"):
    """
    Loads entire ImageContent model sorted in either
    descending or ascending order by time.

    Returns:
      ImageContent object.
    """
    if sort_order == "asc":
        image_content = models.ImageContent.query.order_by(
            models.ImageContent.upload_time.asc())
    elif sort_order == "desc":
        image_content = models.ImageContent.query.order_by(
            models.ImageContent.upload_time.desc())
    else:
        image_content = None
    return image_content


def get_image_contents_by_score(sort_order="asc"):
    """
    Loads entire ImageContent model sorted in either
    descending or ascending order by voting score.

    Returns:
      ImageContent object.
    """
    if sort_order == "asc":
        image_content = models.ImageContent.query.select_from(
            models.ImageContent).outerjoin(
            models.VoteCounter).group_by(
            models.ImageContent).order_by(
            nulls_first(asc(func.sum(models.VoteCounter.vote))))
    elif sort_order == "desc":
        image_content = models.ImageContent.query.select_from(
            models.ImageContent).outerjoin(
            models.VoteCounter).group_by(
            models.ImageContent).order_by(
            nulls_last(desc(func.sum(models.VoteCounter.vote))))
    else:
        image_content = None

    return image_content


def get_image_by_user(user, image_id):
    """
    Loads specific image owned by user if it exists.

    Args:
      user: User object.
      image_id: Image id

    Returns:
      ImageContent object or none.
    """
    # Checks if user object and image_id exists and is valid, else None
    if not user and not image_id:
        return None

    # Get UserContent for user, if it exists
    user_content = models.UserContent().query.filter_by(
        user_id=user.id).one_or_none()

    if not user_content:
        return None

    image_content = models.ImageContent().query.filter_by(
        user_content_id=user_content.id,
        file_id=image_id).one_or_none()

    return image_content


def get_image_contents_by_user(
        username,
        category="upload_time",
        category_filter="desc"):
    """
    Loads a User's ImageContent bases on their username.

    Args:
      username: User name.

    Returns:
      Tuple consisting of None or user object and imagecontent.
    """
    user = auth.models.User().query.filter_by(username=username).first()
    if not user:
        return None, None

    user_content = models.UserContent().query.filter_by(
        user_id=user.id).first()
    if not user_content:
        return user, None
    if category == "upload_time":
        if category_filter == "asc":
            image_content = models.ImageContent.query.filter_by(
                user_content_id=user_content.id).order_by(
                models.ImageContent.upload_time.asc())
        elif category_filter == "desc":
            image_content = models.ImageContent.query.filter_by(
                user_content_id=user_content.id).order_by(
                models.ImageContent.upload_time.desc())
        else:
            image_content = None
    elif category == "score":
        if category_filter == "asc":
            image_content = models.ImageContent.query.select_from(
                models.ImageContent).filter_by(
                user_content_id=user_content.id).outerjoin(
                models.VoteCounter).group_by(
                models.ImageContent).order_by(
                    nulls_first(asc(func.sum(models.VoteCounter.vote)))
            )
        elif category_filter == "desc":
            image_content = models.ImageContent.query.select_from(
                models.ImageContent).filter_by(
                user_content_id=user_content.id).outerjoin(
                models.VoteCounter).group_by(
                models.ImageContent).order_by(
                    nulls_last(desc(func.sum(models.VoteCounter.vote)))
            )
        else:
            image_content = None
    return user, image_content


def get_images_by_tags(tag_name):
    """
    Loads ImageContent by tags.

    Args:
      tags: tags of the images.

    Returns:
      ImageContent object.
    """
    tag = models.Tags().query.filter_by(
        tag_name=tag_name).first()
    if not tag:
        return None

    image_content = models.ImageContent.query.filter(
        models.ImageContent.id.in_(
            [j.image_content_id for j in models.ImageTags().query.filter_by(
                tag_id=tag.id).all()]))

    return image_content


def get_image_content_by_id(image_id):
    """
    Loads ImageContent by file id.

    Args:
      image_id: File id representing the image.

    Returns:
      ImageContent object.
    """
    image_content = models.ImageContent().query.filter_by(
        file_id=image_id).all()
    return image_content


def load_user_images(user_id, image_id):
    """
    Loads ImageContent of user by image_id if any.

    Args:
      user_id: User id.
      image_id: File id representing the image.

    Returns:
      ImageContent object if any else empty list.
    """
    user_content_id = models.UserContent().query.filter_by(
        user_id=user_id).first()

    if user_content_id:
        image_content = models.ImageContent().query.filter_by(
            user_content=user_content_id,
            file_id=image_id).all()
    else:
        image_content = []

    return image_content


def search_by_title(search_value, get_list=True):
    """
    Search ImageContent model by title.

    Args:
      search_value: Search value.

    Returns:
      ImageContent query results.
    """
    search = "%{}%".format(search_value)
    if get_list:
        titles = db.session.query(models.ImageContent).filter(
            models.ImageContent.title.ilike(search)).all()
    else:
        titles = db.session.query(models.ImageContent).filter(
            models.ImageContent.title.ilike(search))
    return titles


def search_by_tags(search_value):
    """
    Search Tags model by tag_name.

    Args:
      search_value: Search value.

    Returns:
      Tags query results.
    """
    search = "%{}%".format(search_value)
    tags = db.session.query(models.Tags).filter(
        models.Tags.tag_name.ilike(search)).all()
    return tags


def create_user_content(user, directory_name):
    """
    Saves a record in UserContent with user and directory
    name where uploads will be stored.

    Args:
      user: User object with user's details i.e user id.
      directory_name: Name of directory where uploads will be stored.

    Returns:
      Boolean indicating result of operation.
    """
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
    """
    Creates or retrieves UserContent if present in the database otherwise
    creates a record.

    Args:
      user: User object with user's details i.e user id.

    Returns:
      UserContent object or None.
    """
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
    """
    Saves user uploaded images and an auto generated thumbnail image in
    their respective folder.

    Args:
      user: User object with user's details i.e user id.
      file: FileStorage object containg image data uploaded.
      image_details: Dict containing information about the uploaded image.

    Returns:
      Boolean indicating result of operation.
    """
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


def image_content_pagination(obj, page=1):
    """
    Takes Models objects and paginates it.

    Args:
      obj: Model object to be paginated.
      page: Integer of the page to be loaded.

    Returns:
      List from the pagination object.
    """
    image_pagination = obj.paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=ERROR_OUT,
        max_per_page=MAX_PER_PAGE)
    return image_pagination.items


def upvote(user, image_file_id):
    """
    Adds upvote metric to the db.

    Args:
      user: User object, specifically current logged in user.
      image_file_id: File ID of image.

    Returns:
      Boolean indicating result of operation.
    """
    upvote_obj = models.VoteCounter().query.filter_by(
        user_id=user.id,
        image_file_id=image_file_id)
    upvote_ = upvote_obj.first()

    if upvote_:
        if upvote_.vote == models.VoteEnum.UPVOTE.value:
            upvote_obj.delete()
        else:
            upvote_.vote = models.VoteEnum.UPVOTE.value
    else:
        upvote = models.VoteCounter(
            user_id=user.id,
            image_file_id=image_file_id,
            vote=models.VoteEnum.UPVOTE.value)

        db.session.add(upvote)

    try:
        db.session.commit()
        return True
    except Exception as e:
        print("An error occured while upvoting content: ", e)
        db.session.rollback()
        return False


def downvote(user, image_file_id):
    """
    Adds downvote metric to the db.

    Args:
      user: User object, specifically current logged in user.
      image_file_id: File ID of image.

    Returns:
      Boolean indicating result of operation.
    """
    downvote_obj = models.VoteCounter().query.filter_by(
        user_id=user.id,
        image_file_id=image_file_id)
    downvote_ = downvote_obj.first()

    if downvote_:
        if downvote_.vote == models.VoteEnum.DOWNVOTE.value:
            downvote_obj.delete()
        else:
            downvote_.vote = models.VoteEnum.DOWNVOTE.value
    else:
        downvote = models.VoteCounter(
            user_id=user.id,
            image_file_id=image_file_id,
            vote=models.VoteEnum.DOWNVOTE.value)

        db.session.add(downvote)

    try:
        db.session.commit()
        return True
    except Exception as e:
        print("An error occured while downvoting content: ", e)
        db.session.rollback()
        return False


def image_metric(image_file_id):
    """
    Loads aggregated ImageContent voting metric filtered by image_id.

    Args:
      image_file_id: Image ID.

    Returns:
      ImageContent aggregated voting metric.
    """
    image_content = models.ImageContent().query.filter_by(
        file_id=image_file_id).first()
    metric_dict = {}
    if image_content:
        vote_enum = models.VoteEnum
        sum_aggr = models.VoteCounter.query.with_entities(
            func.sum(models.VoteCounter.vote).filter(
                models.VoteCounter.image_file_id == image_file_id).label(
                'total'),
            func.sum(models.VoteCounter.vote).filter(
                models.VoteCounter.image_file_id == image_file_id,
                models.VoteCounter.vote == vote_enum.UPVOTE.value).label(
                'upvotes'),
            func.sum(models.VoteCounter.vote).filter(
                models.VoteCounter.image_file_id == image_file_id,
                models.VoteCounter.vote == vote_enum.DOWNVOTE.value).label(
                'downvotes')).first()
        metric_dict['total'] = '--' if sum_aggr.total is None else sum_aggr.total
        metric_dict['upvotes'] = 0 if sum_aggr.upvotes is None \
            else sum_aggr.upvotes
        metric_dict['downvotes'] = 0 if sum_aggr.downvotes is None \
            else sum_aggr.downvotes
        return metric_dict
    else:
        return None


def delete_user_content(user, image_id):
    """
    Delete ImageContent for User and specific Image ID and
    cascade deletes to relevant tables.

    Args:
      user: User Object.
      image_id: Image ID.

    Returns:
      Tuple consisting of boolean indicating status of operation,
      image_name and user_directory if successful.
    """
    user_content = models.UserContent().query.filter_by(
        user_id=user.id).first()

    if user_content:
        image_content = models.ImageContent().query.filter_by(
            file_id=image_id)
        user_directory = user_content.content_location
        if image_content.first():
            # Gets title name of image to delete.
            image_name = image_content.first().title

            # Confirms if logged in user owns the image.
            image_content = image_content.filter_by(
                user_content_id=user_content.id)

            # TODO: Implement cascade delete to avoid this.
            # VoteCounter records for image.
            vote_counter = models.VoteCounter().query.filter_by(
                image_file_id=image_content.first().file_id)
            if image_content:
                try:
                    # Deletes Vote counter for image content.
                    vote_counter.delete()

                    # Delete image content.
                    image_content.delete()

                    # Commit session.
                    db.session.commit()

                    return True, image_name, user_directory
                except Exception as e:
                    # Rollback session.
                    db.session.rollback()

                    print("An error occured while deleting image: ", e)
                    return False, image_name, user_directory
            else:
                return False, image_name, user_directory
        else:
            return False, None, None
    else:
        return False, None, None
