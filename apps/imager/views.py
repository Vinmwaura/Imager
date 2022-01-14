import os

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
    send_from_directory,
    abort)
from flask_login import (
    login_required,
    current_user)
from werkzeug.utils import secure_filename

from . import imager_bp
from .forms import *
from .controllers import *


def get_filter_options(category, sort_order):
    """
    Filter options for gallery.

    Args:
      category: Filter option to use on image.
      sort_order: Sort oprions to use with filter.

    Returns:
      Dict with filter options to be used on the html.
    """
    filter_options = {}
    filter_options["categories"] = [
        {"name": "Upload Time", "value": "upload_time"},
        {"name": "Score", "value": "score"}
    ]

    if category == "upload_time":
        filter_options["selected_category"] = "Upload Time"
        if sort_order == "desc":
            filter_options["selected_filter"] = "Newest to Oldest"
        elif sort_order == "asc":
            filter_options["selected_filter"] = "Oldest to Newest"
        else:
            filter_options["selected_filter"] = ""

        filter_options['options'] = [
            {
                "value": "Newest to Oldest",
                "filter": "desc",
                "category": "upload_time"},
            {
                "value": "Oldest to Newest",
                "filter": "asc",
                "category": "upload_time"}
        ]
    elif category == "score":
        filter_options['selected_category'] = "Score"
        if sort_order == "desc":
            filter_options["selected_filter"] = "Highest"
        elif sort_order == "asc":
            filter_options["selected_filter"] = "Lowest"
        else:
            filter_options["selected_filter"] = ""

        filter_options['options'] = [
            {"value": "Highest", "filter": "desc", "category": "score"},
            {"value": "Lowest", "filter": "asc", "category": "score"}
        ]
    else:
        pass
    return filter_options


@imager_bp.route("/about")
def about():
    return render_template("imager/about.html")


@imager_bp.route("/")
@imager_bp.route('/<string:category>')
@imager_bp.route('/<string:category>/<string:category_filter>')
def index(category="upload_time", category_filter="desc"):
    page = request.args.get('page', 1, type=int)

    if category_filter not in ['asc', 'desc']:
        abort(404)

    if category == "upload_time":
        if category_filter is None:
            category_filter = "asc"  # Default value if no parameter.
        image_contents = get_image_contents_by_time(category_filter)
    elif category == "score":
        if category_filter is None:
            category_filter = "desc"  # Default value if no parameter.
        image_contents = get_image_contents_by_score(category_filter)
    elif category == "":
        image_contents = get_image_contents_by_time()
    else:
        abort(404)

    if not image_contents:
        images_pagination = []
        data_dict = []
    else:
        images_pagination = image_content_pagination(
            image_contents,
            page=page)
        data_dict = get_image_details(current_user, images_pagination.items)

    filter_options = get_filter_options(category, category_filter)
    return render_template(
        "imager/index.html",
        images=data_dict,
        images_pagination=images_pagination,
        filter_options=filter_options)


@imager_bp.route("/settings")
@login_required
def settings():
    from .. import api
    created_clients = api.controllers.load_clients_created(current_user)
    clients_used = api.controllers.load_clients_used(current_user)
    return render_template(
        'imager/settings.html',
        created_clients=created_clients,
        clients_used=clients_used)


@imager_bp.route("/settings/delete/<string:client_id>")
@login_required
def settings_delete_client(client_id):
    from .. import api
    user = current_user
    status = api.controllers.delete_client(user, client_id)
    if status:
        flash("Successfully deleted client: {}".format(client_id), 'success')
        return redirect(url_for('imager.settings') + '#application')
    else:
        flash("An error occured deleting client: {}".format(
            client_id), 'error')
        return redirect(url_for('imager.settings') + '#application')


@imager_bp.route("/settings/revoke/<string:token_id>")
@login_required
def settings_revoke_client(token_id):
    """
    models.OAuth2Token.query.filter_by(
        user_id=user.id,
        revoked=False).all()
    """
    from .. import api
    user = current_user
    status = api.controllers.manual_revoke_token(user, token_id)
    if status:
        flash('Successfully revoked token', 'success')
        return redirect(url_for('imager.settings'))
    else:
        flash('An error occured revoking token', 'error')
        return redirect(url_for('imager.settings'))


@imager_bp.route("/upload", methods=["GET", "POST"])
@login_required
@can_post_main_dashboard
def upload_images():
    upload_file_form = UploadFileForm()
    if upload_file_form.validate_on_submit():
        uploaded_file = upload_file_form.file.data

        filename = secure_filename(uploaded_file.filename)

        if filename != "":
            # File Extension from filename
            file_ext = os.path.splitext(filename)[1]
            image_extensions = current_app.config['UPLOAD_EXTENSIONS']

            if file_ext not in image_extensions:
                flash(
                    "Image type is not valid, only supports {}!".format(
                        ", ".join(image_extensions)), "error")
                return redirect(url_for('imager.upload_images'))

            # Security check to ensure image type matches data uploaded
            image_format = validate_image(uploaded_file.stream)

            # .JPG == .JPEG (Interchangeable)
            jpg_formats = [".jpg", ".jpeg"]
            if image_format in jpg_formats and file_ext in jpg_formats:
                pass
            elif file_ext != image_format:
                flash("File uploaded is not valid!", "error")
                return redirect(url_for('imager.upload_images'))

            # Check if user has a folder for storing their content.
            # Create a folder for user if first time posting content.
            user_content = create_or_get_user_content(current_user)

            if not user_content:
                return SERVER_ERROR, 500

            image_details = {
                "title": request.form["title"]
            }

            status = save_user_image(
                current_user,
                uploaded_file,
                image_details)
            if not status:
                # return SERVER_ERROR, 500
                flash(SERVER_ERROR, "error")
            else:
                flash("Image Successfully added.", "success")
            return redirect(url_for('imager.index'))

    return render_template(
        "imager/upload.html",
        form=upload_file_form)


@imager_bp.route("/upload/image/<string:image_id>")
def load_image_by_id(image_id):
    image_content = get_image_content_by_id(image_id)
    if image_content:
        # Gets filenames and filepath using ImageContent object.
        folder_path, image_filenames = get_image_file_paths(
            image_content[0],
            current_app.config["UPLOAD_PATH"])

        # Checks if actual file exists.
        if len(image_filenames) == 0:
            abort(404)
        # Check if duplicate files with same ID exists.
        elif len(image_filenames) > 1:
            # Log errors here, duplicates IDS not allowed.
            print("Duplicate file {} found".format(file_regex))
            abort(404)
        else:
            return send_from_directory(folder_path, image_filenames[0])

    abort(404)


@imager_bp.route("/upload/thumbnail/<string:image_id>")
def load_thumbnail_by_id(image_id):
    image_content = get_image_content_by_id(image_id)
    if image_content:
        # Gets filenames and filepath using ImageContent object.
        folder_path, image_filenames = get_image_file_paths(
            image_content[0],
            current_app.config["UPLOAD_PATH"])

        # Checks if actual file exists.
        if len(image_filenames) == 0:
            abort(404)
        # Check if duplicate files with same ID exists.
        elif len(image_filenames) > 1:
            # Log errors here, duplicates IDS not allowed.
            print("Duplicate file {} found".format(file_regex))
            abort(404)
        else:
            return send_from_directory(
                os.path.join(
                    folder_path,
                    "thumbnails"),
                image_filenames[0])

    abort(404)


@imager_bp.route("/gallery/<string:image_id>")
def load_gallery_image(image_id):
    image_content = get_image_content_by_id(image_id)
    if image_content:
        data_dict = get_image_details(current_user, image_content)
        return render_template(
            "imager/image_gallery.html",
            image=data_dict[0])

    abort(404)


@imager_bp.route("/gallery/search")
def load_gallery_search():
    query = request.args.get('q', None, type=str)
    page = request.args.get('page', 1, type=int)

    if query:
        image_contents = search_by_title(query, False)
    else:
        image_contents = []

    if not image_contents:
        images_pagination = []
        data_dict = []
    else:
        images_pagination = image_content_pagination(
            image_contents,
            page=page)
        data_dict = get_image_details(current_user, images_pagination.items)
    return render_template(
        "imager/search_result.html",
        q="q=" + query,
        images=data_dict,
        image_contents_len=len(image_contents.all()),
        images_pagination=images_pagination)


@imager_bp.route("/edit/gallery/<string:image_id>", methods=["GET", "POST"])
@login_required
def edit_gallery(image_id):
    user = current_user
    image_content = get_image_by_user(user, image_id)
    if image_content:
        edit_image_uploaded = EditImageForm(
            title=image_content.title)
        if edit_image_uploaded.validate_on_submit():
            gallery_title = request.form["title"]
            if gallery_title != image_content.title:
                data_dict = {'title': gallery_title}
                updated_gallery = update_gallery(
                    image_content,
                    data_dict)
                if updated_gallery:
                    flash(
                        "Successfully updated to \'{}\'".format(
                            image_content.title), "success")
                else:
                    flash("An error occured while updating {}".format(
                        image_content.title))
            else:
                flash("No change detected", "info")
            return redirect(url_for('imager.user_profile'))
        return render_template(
            "imager/edit_image.html",
            image=image_content,
            form=edit_image_uploaded)
    else:
        abort(404)


@imager_bp.route("/gallery/user/<string:username>")
@imager_bp.route('/gallery/user/<string:username>/<string:category>')
@imager_bp.route('/gallery/user/<string:username>/<string:category>/<string:category_filter>')
def load_images_by_username(
        username,
        category="upload_time",
        category_filter="desc"):
    page = request.args.get('page', 1, type=int)

    user, image_content = get_image_contents_by_user(
        username,
        category,
        category_filter)
    # If no user is found, 404 Page not found
    if user is None:
        abort(404)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images_pagination = []
        data_dict = []
    else:
        images_pagination = image_content_pagination(image_content, page=page)
        data_dict = get_image_details(current_user, images_pagination.items)
    filter_options = get_filter_options(category, category_filter)
    return render_template(
        "imager/user_gallery.html",
        images=data_dict,
        images_pagination=images_pagination,
        filter_options=filter_options,
        user=user)


@imager_bp.route("/user/profile", methods=["GET", "POST"])
@imager_bp.route('/user/profile/<string:category>')
@imager_bp.route('/user/profile/<string:category>/<string:category_filter>')
@login_required
def user_profile(category="upload_time", category_filter="desc"):
    delete_form = DeleteForms()
    if delete_form.validate_on_submit():
        if "image_id" in request.form:
            image_args = request.form["image_id"]
            image_ids = image_args.split(",")
            try:
                for image_id in image_ids:
                    status, image_name, user_directory = delete_user_content(
                        current_user, image_id)
                    if status is True and image_name:
                        flash(
                            "Successfully deleted image \'{}\'".format(
                                image_name),
                            "success")

                        # Delete image file from server
                        file_path = current_app.config["UPLOAD_PATH"]
                        status = delete_image_file(
                            file_path,
                            user_directory,
                            image_id)
                    elif status is False and image_name:
                        flash(
                            "An error occured and image \'{}\' couldn't be \
                            deleted.".format(
                                image_name), "error")
                    else:
                        flash(
                            "An error occured on the server, and operation \
                            couldn't be performed.", "error")
            except Exception as e:
                print("An exception occured while deleting images: ", e)
                flash("An error occured while deleting", "error")
        else:
            flash("No arguments passed!", "error")

        return redirect(url_for('imager.user_profile'))
    page = request.args.get('page', 1, type=int)

    user, image_content = get_image_contents_by_user(
        current_user.username,
        category,
        category_filter)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images_pagination = []
        data_dict = []
    else:
        images_pagination = image_content_pagination(image_content, page=page)
        data_dict = get_image_details(current_user, images_pagination.items)
    filter_options = get_filter_options(category, category_filter)
    return render_template(
        "imager/user_profile.html",
        images=data_dict,
        images_pagination=images_pagination,
        user=user,
        filter_options=filter_options,
        form=delete_form)


@imager_bp.route("/gallery/tag/<string:tag_name>")
def load_images_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    image_content = get_images_by_tags(tag_name)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images_pagination = []
    else:
        images_pagination = image_content_pagination(
            image_content,
            page=page).items
    return render_template(
        "imager/user_gallery.html",
        images=images_pagination,
        images_pagination=images_pagination)


@imager_bp.route("/upvote", methods=["POST"])
def upvote_counter():
    if current_user.is_anonymous:
        # TODO: Add next to return user to previous page
        return redirect(url_for('auth.login'))

    image_file_id = request.form.get('image_id', None)
    if image_file_id:
        upvote_status = upvote(current_user, image_file_id)
        metric_data = image_metric(image_file_id)
        metric_data["status"] = upvote_status
        return jsonify(metric_data)
    else:
        return "Invalid parameter.", 400


@imager_bp.route("/downvote", methods=["POST"])
def downvote_counter():
    if current_user.is_anonymous:
        # TODO: Add next to return user to previous page
        return redirect(url_for('auth.login'))

    image_file_id = request.form.get('image_id', None)
    if image_file_id:
        downvote_status = downvote(current_user, image_file_id)
        metric_data = image_metric(image_file_id)
        metric_data["status"] = downvote_status

        return jsonify(metric_data)
    else:
        return "Invalid parameter.", 400


@imager_bp.route("/metric/<string:image_file_id>")
def vote_metric(image_file_id):
    metric_data = image_metric(image_file_id)
    if metric_data:
        return jsonify(metric_data)
    else:
        return "Invalid parameter.", 400
