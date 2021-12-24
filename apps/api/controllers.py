import time

from .. import auth
from .. import imager
from . import models

from .. import db

from .. import oauth2_config
from authlib.oauth2 import OAuth2Error
from authlib.integrations.flask_oauth2 import current_token

from flask import current_app
from sqlalchemy.sql import func
from sqlalchemy import asc, desc, nulls_first, nulls_last

from werkzeug.security import gen_salt

imager_models = imager.models
auth_models = auth.models
api_models = models


def validate_consent_request(user):
    try:
        grant = oauth2_config.authorization.validate_consent_request(end_user=user)
        return grant
    except OAuth2Error as error:
        print("An error occured while validating consent request: ", error.error)
        return error.error


def create_authorization_response(grant_user):
    auth_response = oauth2_config.authorization.create_authorization_response(
        grant_user=grant_user)
    return auth_response


def load_clients(user):
    clients = models.OAuth2Client.query.filter_by(user_id=user.id).all()
    return clients

def issue_token():
    return oauth2_config.authorization.create_token_response()

def revoke_token():
    return oauth2_config.authorization.create_endpoint_response('revocation')


def create_auth_client(user, client_metadata):
    try:
        client_id = gen_salt(24)
        client_id_issued_at = int(time.time())
        client = api_models.OAuth2Client(
            client_id=client_id,
            client_id_issued_at=client_id_issued_at,
            user_id=user.get_user_id(),)
        client.set_client_metadata(client_metadata)

        if client_metadata['token_endpoint_auth_method'] == 'none':
            client.client_secret = ''
        else:
            client.client_secret = gen_salt(48)

        db.session.add(client)
        db.session.commit()
        return client
    except Exception as e:
        db.session.rollback()
        print("An error occured while creating auth client: ", e)
        return None
    

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
        per_page=current_app.config["API_PER_PAGE"],
        error_out=False,
        max_per_page=current_app.config["API_MAX_PER_PAGE"])
    return image_pagination.items


def get_image_contents_by_id(id):
    image_content = imager_models.ImageContent.query.filter_by(file_id=id)
    return image_content


def get_image_contents_by_time(sort_order="asc"):
    """
    Loads entire ImageContent model sorted in either
    descending or ascending order by time.

    Returns:
      ImageContent object.
    """
    if sort_order == "asc":
        image_content = imager_models.ImageContent.query.order_by(
            imager_models.ImageContent.upload_time.asc())
    elif sort_order == "desc":
        image_content = imager_models.ImageContent.query.order_by(
            imager_models.ImageContent.upload_time.desc())
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
        image_content = imager_models.ImageContent.query.select_from(
            imager_models.ImageContent).outerjoin(
            imager_models.VoteCounter).group_by(
            imager_models.ImageContent).order_by(
            nulls_first(asc(func.sum(imager_models.VoteCounter.vote))))
    elif sort_order == "desc":
        image_content = imager_models.ImageContent.query.select_from(
            imager_models.ImageContent).outerjoin(
            imager_models.VoteCounter).group_by(
            imager_models.ImageContent).order_by(
            nulls_last(desc(func.sum(imager_models.VoteCounter.vote))))
    else:
        image_content = None

    return image_content


# TODO: Use user id instead of name.
def get_image_contents_by_user(username):
    """
    Loads a User's ImageContent bases on their username.

    Args:
      username: User name.

    Returns:
      Tuple imagecontent if user exists.
    """
    user = auth_models.User().query.filter_by(username=username).one_or_none()
    if user is None:
        return None

    user_content = imager_models.UserContent().query.filter_by(
        user_id=user.id).one_or_none()
    if not user_content:
        return None

    image_content = imager_models.ImageContent().query.filter_by(
        user_content_id=user_content.id)
    return image_content


def image_metric(image_file_id):
    image_content = imager_models.ImageContent().query.filter_by(
        file_id=image_file_id).first()
    metric_dict = {}
    if image_content:
        vote_enum = imager_models.VoteEnum
        sum_aggr = imager_models.VoteCounter.query.with_entities(
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_file_id
            ).label(
                'total'),
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_file_id,
                imager_models.VoteCounter.vote == vote_enum.UPVOTE.value
            ).label(
                'upvotes'),
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_file_id,
                imager_models.VoteCounter.vote == vote_enum.DOWNVOTE.value
            ).label(
                'downvotes')).first()
        metric_dict['total'] = sum_aggr.total
        metric_dict['upvotes'] = sum_aggr.upvotes
        metric_dict['downvotes'] = sum_aggr.downvotes
        return metric_dict
    else:
        return None
