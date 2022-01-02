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


def delete_client(user, client_id):
    """
    Manually deletes Clients and tokens in the database.

    Args:
      user: Current User object logged in.
      client_id: Client id to be deleted.

    Returns:
      Boolean indicating status of the operation.
    """
    try:
        client = models.OAuth2Client.query.filter_by(
            user_id=user.id,
            client_id=client_id).one_or_none()

        if client is None:
            return False
        else:
            # Hack to allow cascade delete.
            tokens = models.OAuth2Token.query.filter_by(
                user_id=user.id,
                client_id=client.client_id).all()
            for token in tokens:
                db.session.delete(token)

            codes = models.OAuth2AuthorizationCode.query.filter_by(
                user_id=user.id,
                client_id=client.client_id).all()
            for code in codes:
                db.session.delete(code)

            db.session.delete(client)

            # Commit delete operations.
            db.session.commit()

            return True
    except Exception as e:
        db.session.rollback()
        print("An error occured while deleting client {}: {}".format(
            client_id,
            e))
        return False


def manual_revoke_token(user, token_id):
    """
    Revokes access token in use.

    Args:
      user: Current User object logged in.
      token_id: Token id to be revoked.

    Returns:
      Boolean indicating status of the operation.
    """
    try:
        token = models.OAuth2Token.query.filter_by(
            user_id=user.id,
            id=token_id).one_or_none()

        if token is None:
            return False
        else:
            token.revoked = True
            db.session.add(token)
            db.session.commit()
            return True
    except Exception as e:
        db.session.rollback()
        print("An error occured while revoking token: ", e)
        return False


def validate_consent_request(user):
    """
    Validates user consent.

    Args:
      user: Current User object who needs to grant access.

    Returns:
      Grant object or error if exception occurs.
    """
    try:
        grant = oauth2_config.authorization.validate_consent_request(end_user=user)
        return grant
    except OAuth2Error as error:
        print("An error occured while validating consent request: ", error.error)
        return error.error


def create_authorization_response(grant_user):
    """
    Creates authorization response.

    Args:
      grant_user: Resource Owner(User) object who is granting client access.

    Returns:
      Response dict.
    """
    auth_response = oauth2_config.authorization.create_authorization_response(
        grant_user=grant_user)
    return auth_response


def load_clients_created(user):
    """
    Loads clients created by the user.

    Args:
      user: Current logged in user.

    Returns:
      Clients owned by the user.
    """
    clients = models.OAuth2Client.query.filter_by(
        user_id=user.id).order_by(
            models.OAuth2Client.client_id_issued_at.desc()).all()
    return clients


def load_clients_used(user):
    """
    Loads clients granted access by the user.

    Args:
      user: Current logged in user.

    Returns:
      Clients owned by the user and given access.
    """
    client_created = models.OAuth2Token.query.filter_by(
        user_id=user.id,
        revoked=False).all()
    clients_used = models.OAuth2Client.query.filter(
        models.OAuth2Client.client_id.in_(
            (x_.client_id for x_ in client_created))).order_by(
            models.OAuth2Client.client_id_issued_at.desc()).all()
    data = []
    for index, _ in enumerate(clients_used):
        data.append({
            "name": clients_used[index].client_metadata['client_name'],
            "token_id": client_created[index].id
        })
    return data


def issue_token():
    """
    Issues a token to the user.

    Returns:
      Repsonse.
    """
    return oauth2_config.authorization.create_token_response()


def revoke_token():
    """
    Revokes a token.

    Returns:
      Repsonse.
    """
    return oauth2_config.authorization.create_endpoint_response('revocation')


def create_auth_client(user, client_metadata):
    """
    Loads clients granted access by the user.

    Args:
      user: Current logged in user.
      client_metadata: Dict containing client details

    Returns:
      Created client or None if error occurs.
    """
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


def get_image_contents_by_id(image_id):
    """
    Loads specific ImageContent model filtered by id.

    Args:
      image_id: Image ID.

    Returns:
      ImageContent object.
    """
    image_content = imager_models.ImageContent.query.filter_by(
        file_id=image_id)
    return image_content


def get_image_contents_by_time(sort_order="asc"):
    """
    Loads entire ImageContent model sorted in either
    descending or ascending order by time.
    
    Args:
      sort_order: Sort type i.e 'asc' and 'desc'.

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
    
    Args:
      sort_order: Sort type i.e 'asc' and 'desc'.

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


def image_metric(image_id):
    """
    Loads aggregated ImageContent voting metric filtered by image_id.

    Args:
      image_id: Image ID.

    Returns:
      ImageContent aggregated voting metric.
    """
    image_content = imager_models.ImageContent().query.filter_by(
        file_id=image_id).first()
    metric_dict = {}
    if image_content:
        vote_enum = imager_models.VoteEnum
        sum_aggr = imager_models.VoteCounter.query.with_entities(
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_id
            ).label(
                'total'),
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_id,
                imager_models.VoteCounter.vote == vote_enum.UPVOTE.value
            ).label(
                'upvotes'),
            func.sum(imager_models.VoteCounter.vote).filter(
                imager_models.VoteCounter.image_file_id == image_id,
                imager_models.VoteCounter.vote == vote_enum.DOWNVOTE.value
            ).label(
                'downvotes')).first()
        metric_dict['total'] = sum_aggr.total
        metric_dict['upvotes'] = sum_aggr.upvotes
        metric_dict['downvotes'] = sum_aggr.downvotes
        return metric_dict
    else:
        return None
