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


def get_image_details(user, images):
    data_dict = []
    for image in images:
        temp_dict = {}
        temp_dict["uploaded_by"] = image.user_content.user.username
        temp_dict["title"] = image.title
        temp_dict["file_id"] = image.file_id
        temp_dict["voter_count"] = image_metric(image.file_id)

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


@imager_bp.route("/")
def index():
    page = request.args.get('page', 1, type=int)

    image_content = get_image_contents_by_time()
    if not image_content:
        images = []
    else:
        images = image_content_pagination(image_content, page=page)

    data_dict = get_image_details(current_user, images)
    return render_template(
        "imager/index.html",
        images=data_dict)


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
            if file_ext != validate_image(uploaded_file.stream):
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
                flash("Image Successfully added.", "info")
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


@imager_bp.route("/edit/gallery/<string:image_id>", methods=["GET", "POST"])
@login_required
def edit_gallery(image_id):
    image_content = get_image_content_by_id(image_id)
    if image_content:
        edit_image_uploaded = EditImageForm(
            title=image_content[0].title)

        if edit_image_uploaded.validate_on_submit():
            gallery_title = request.form["title"]

            if gallery_title != image_content[0].title:
                image_content[0].title = gallery_title

                try:
                    # Commit Session
                    db.session.commit()
                    flash(
                        "Successfully updated to \'{}\'".format(
                            image_content[0].title), "success")
                except Exception as e:
                    # Rollback session
                    db.session.rollback()
                    # TODO: Log error message properly
                    print("An error occured while commiting Role: ", e)
                    flash("An error occured while updating {}.".format(
                        image_content[0].title))
            else:
                flash("No change detected", "info")

            return redirect(url_for('imager.user_profile'))

        return render_template(
            "imager/edit_image.html",
            image=image_content[0],
            form=edit_image_uploaded)
    abort(404)


@imager_bp.route("/gallery/user/<string:username>")
def load_images_by_username(username):
    page = request.args.get('page', 1, type=int)

    user, image_content = get_image_contents_by_user(username)
    # If no user is found, 404 Page not found
    if user is None:
        abort(404)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images = []
    else:
        images = image_content_pagination(image_content, page=page)

    data_dict = get_image_details(current_user, images)
    return render_template(
        "imager/user_gallery.html",
        images=data_dict,
        user=user)


@imager_bp.route("/user/profile", methods=["GET", "POST"])
@login_required
def user_profile():
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
            return redirect(url_for('imager.user_profile'))
        else:
            flash("No arguments passed!", "error")
    page = request.args.get('page', 1, type=int)

    user, image_content = get_image_contents_by_user(current_user.username)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images = []
    else:
        images = image_content_pagination(image_content, page=page)

    data_dict = get_image_details(current_user, images)
    return render_template(
        "imager/user_profile.html",
        images=data_dict,
        user=user,
        form=delete_form)


@imager_bp.route("/gallery/tag/<string:tag_name>")
def load_images_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    image_content = get_images_by_tags(tag_name)

    # If user has no uploaded images, return empty images
    if image_content is None:
        images = []
    else:
        images = image_content_pagination(image_content, page=page)
    return render_template(
        "imager/user_gallery.html",
        images=images)


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
