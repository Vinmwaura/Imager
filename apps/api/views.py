import os
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
def oauth_authorize():
    if request.method == 'GET':
        grant = validate_consent_request(current_user)
        if isinstance(grant, str):
            return grant
        else:
            return render_template(
                'api/authorize.html',
                grant=grant)
    elif request.method == 'POST':
        if request.form['submit'] == 'allow':
            grant_user = current_user
        elif request.form['submit'] == 'deny':
            grant_user = None
        auth_resp = create_authorization_response(grant_user)
        return auth_resp


@api_bp.route('/create_client', methods=['GET', 'POST'])
@login_required
def create_client():
    client = []
    addclient_form = AddClientForm()
    if addclient_form.validate_on_submit():
        form = request.form
        client_metadata = {
            "client_name": form["client_name"],
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


@api_bp.route('/search/<string:search_value>')
@csrf.exempt
def search(search_value):
    api_data = {}
    api_data["results"] = {}

    # Search by username
    from .. import auth
    search_user_results = auth.controllers.search_by_username(search_value)
    api_data["results"]['users'] = []
    for user in search_user_results:
        data_dict = {}
        data_dict["username"] = user.username
        data_dict["first_name"] = user.first_name
        data_dict["last_name"] = user.last_name
        data_dict["email"] = user.email

        api_data["results"]['users'].append(data_dict)

    from .. import imager as img_
    # Search by image title
    search_title_results = img_.controllers.search_by_title(search_value)
    api_data["results"]['image'] = []
    for image in search_title_results:
        data_dict = {}
        data_dict["title"] = image.title
        data_dict["image_id"] = image.file_id
        data_dict["upload_time"] = image.upload_time
        data_dict["description"] = image.description
        data_dict["metric"] = image_metric(image.file_id)
        data_dict["url"] = url_for(
            'imager.load_image_by_id', image_id=image.file_id)

        api_data["results"]['image'].append(data_dict)

    # Search by tag
    search_tag_results = img_.controllers.search_by_tags(search_value)
    api_data["results"]['tags'] = []
    for tag in search_tag_results:
        data_dict = {}
        data_dict["id"] = tag.id
        data_dict["tag_name"] = tag.tag_name
        api_data["results"]['tags'].append(data_dict)

    api_data['status'] = 200
    return jsonify(api_data), 200


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


@api_bp.route('/upload', methods=["POST"])
@oauth2.require_oauth()
@csrf.exempt
def upload_image():
    from .. import imager as img_

    if 'file' not in request.files:
        return jsonify(
            message='Requires file attribute for image.',
            status=400), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify(
            message='No file selected for uploading.',
            status=400), 400

    # File Extension from filename.
    file_ext = os.path.splitext(file.filename)[1]
    image_extensions = current_app.config['UPLOAD_EXTENSIONS']

    if file_ext not in image_extensions:
        resp = jsonify(
            message="Image type is not valid, only supports {}!".format(
                ", ".join(image_extensions)),
            status=422)
        return resp, 422

    # Security check to ensure image type matches data uploaded.
    image_format = img_.controllers.validate_image(file.stream)

    # .JPG == .JPEG (Interchangeable)
    jpg_formats = [".jpg", ".jpeg"]
    if image_format in jpg_formats and file_ext in jpg_formats:
        pass
    elif file_ext != image_format:
        return jsonify(
            message="File uploaded is invalid!",
            status=422), 422

    # Check if image title is valid and present.
    if 'title' not in request.form:
        return jsonify(
            message='Requires title attribute.',
            status=400), 400

    img_title = request.form['title']
    title_len = len(img_title)
    if img_.utils.MIN_TITLE_LENGTH < title_len > img_.utils.MAX_TITLE_LENGTH:
        return jsonify(
            message=img_.utils.INVALID_TITLE_LENGTH,
            status=400), 400

    # Check if user has a folder for storing their content.
    # Create a folder for user if first time posting content.
    user = current_token.user
    user_content = img_.controllers.create_or_get_user_content(user)
    if not user_content:
        return jsonify(
            message="An error occured in the server, upload failed.",
            status=500), 500

    image_details = {
        "title": img_title
    }

    status = img_.controllers.save_user_image(
        user,
        file,
        image_details)
    if not status:
        return jsonify(
            message="An error occured in the server, upload failed.",
            status=500), 500
    else:
        return jsonify(
            message="Image Successfully added.",
            status=200), 200


@api_bp.route('/delete/image/<string:image_id>', methods=["DELETE"])
@oauth2.require_oauth()
@csrf.exempt
def delete_image_by_id(image_id):
    api_status = 200

    user = current_token.user

    from .. import imager as img_
    status, image_name, user_directory = img_.controllers.delete_user_content(
        user, image_id)
    if status is True and image_name:
        # Delete image file from server
        file_path = current_app.config["UPLOAD_PATH"]
        del_file_status = img_.controllers.delete_image_file(
            file_path,
            user_directory,
            image_id)
        if not del_file_status:
            print("An error occured deleting file {}".format(
                os.path.join(file_path, image_id)))
        message = "Successfully deleted image \'{}\'".format(image_name)
    elif status is False and image_name:
        message = "An error occured and image \'{}\' couldn't be \
            deleted.".format(image_name)
    else:
        api_status = 500
        message = "An error occured on the server, and task"\
            " couldn't be performed."

    return jsonify(
        status=api_status,
        message=message), api_status


@api_bp.route(
    '/image/<string:image_id>/vote/<string:vote_action>',
    methods=["POST"])
@oauth2.require_oauth()
@csrf.exempt
def vote_counter(image_id, vote_action):
    user = current_token.user

    from .. import imager as img_

    # Checks if image id is valid and image exists.
    image_exists = img_.controllers.get_image_content_by_id(image_id)
    if len(image_exists) == 0:
        return jsonify(message="Image doesn't exist.", status=404), 404

    # Perform vote action.
    if vote_action == "up":
        vote_status = img_.controllers.upvote(user, image_id)
    elif vote_action == "down":
        vote_status = img_.controllers.downvote(user, image_id)
    else:
        return jsonify(message="Invalid parameter.", status=400), 400

    # Get metric information.
    metric_data = None
    if vote_status:
        metric_data = img_.controllers.image_metric(image_id)
        if metric_data is not None:
            metric_data["status"] = 200
            metric_data["message"] = "Success."

    # Check if error occured on the server, return 500 status code if so.
    if vote_status is False or metric_data is None:
        metric_data = {}
        metric_data["status"] = 500
        metric_data["message"] = "An error occured in the server and"\
            " operation could not be performed."

    return jsonify(metric_data), metric_data["status"]
