import time
from flask import (
    jsonify,
    render_template,
    current_app,
    url_for,
    redirect,
    request)

from . import api_bp
from .controllers import *
from .forms import *

from .. import csrf

from flask_login import (
    login_required,
    current_user)

from authlib.integrations.flask_oauth2 import current_token
from .. import oauth2_config as oauth2


@api_bp.route('/')
def api_index():
    return render_template('api/api_docs.html')


@api_bp.route('/oauth/authorize', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def oauth_authorize():
    if request.method == 'GET':
        grant = validate_consent_request(current_user)
        if isinstance(grant, str):
            return grant
        else:
            return render_template(
                'api/authorize.html',
                user=current_user,
                grant=grant)
    elif request.method == 'POST':
        if request.form['submit'] == 'allow':
            grant_user = current_user
        elif request.form['submit'] == 'deny':
            grant_user = None
        auth_resp = create_authorization_response(grant_user)
        return auth_resp


@api_bp.route("/gallery")
@api_bp.route("/gallery/<string:category>")
@api_bp.route("/gallery/<string:category>/<string:category_filter>")
def load_gallery(category="upload_time", category_filter=None):
    # Assumes no issue will occur otherwise will be changed.
    message = "Successful."
    api_status = 200

    # Request Arguments
    page = request.args.get("p", default=1, type=int)

    if category == "upload_time":
        if category_filter is None:
            category_filter = "desc"  # Default value if no parameter.
        image_contents = get_image_contents_by_time(category_filter)
    elif category == "score":
        if category_filter is None:
            category_filter = "desc"  # Default value if no parameter.
        image_contents = get_image_contents_by_score(category_filter)
    elif category == "image":
        if category_filter is None:
            image_contents = None
            message = "Requires image id."
            api_status = 400
        else:
            image_contents = get_image_contents_by_id(category_filter)
    elif category == "user":
        if category_filter is None:
            message = "Requires username."
            api_status = 400
            image_contents = None
        else:
            image_contents = get_image_contents_by_user(category_filter)
    else:
        image_contents = None
        api_status = 400
        message = "Invalid requests."

    api_data = []
    if image_contents:
        try:
            image_contents = image_content_pagination(image_contents, page)
            for image_content in image_contents:
                data_dict = {}
                data_dict["title"] = image_content.title
                data_dict["image_id"] = image_content.file_id
                data_dict["upload_time"] = image_content.upload_time
                data_dict["description"] = image_content.description
                data_dict["metric"] = image_metric(image_content.file_id)
                data_dict["url"] = url_for(
                    'imager.load_image_by_id', image_id=image_content.file_id)
                api_data.append(data_dict)
        except Exception as e:
            print("An Error occured while appending to gallery api: ", e)
            api_data = []
            message = "Error occured on the server. Please try again."
            api_status = 500

    api_dict = {
        "data": api_data,
        "message": message,
        "status": api_status
    }
    return jsonify(api_dict)


@api_bp.route('/create_client', methods=['GET', 'POST'])
@login_required
def create_client():
    client = []
    addclient_form = AddClientForm()
    if addclient_form.validate_on_submit():
        form = request.form
        client_metadata = {
            "client_name": form["application_name"],
            "redirect_uris": [form["redirect_uris"] or url_for(
                'imager.index')],
            "grant_types": ['authorization_code'],
            "response_types": "code",
            "token_endpoint_auth_method": form["token_endpoint_auth_method"]
        }
        client = create_auth_client(current_user, client_metadata)
        if client is None:
            flash("An Error occured creating application, \
                please try again in a while.")

    return render_template(
        "api/add_client.html",
        form=addclient_form,
        client=client)


@api_bp.route('/oauth/token', methods=['POST'])
@csrf.exempt
def oauth_token():
    token = issue_token()
    return token


@api_bp.route('/oauth/revoke', methods=['POST'])
@csrf.exempt
def oauth_revoke():
    revoke = revoke_token()
    return jsonify(status=revoke.status_code, message=revoke.status)


@api_bp.route('/me')
@oauth2.require_oauth()
def api_me():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)
