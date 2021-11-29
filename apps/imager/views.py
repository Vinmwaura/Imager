import os
import glob

from functools import wraps

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
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


PERMISSION_DENIED = "You don't have permission to post to this page,"\
    " Contact Administrator if you think you should."
SERVER_ERROR = "An error occured in the server"


# Assumes you can view admin dashboard to insert
def can_post_main_dashboard(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_post_main_dashboard():
            return func(*args, **kwargs)
        else:
            return PERMISSION_DENIED, 403
    return inner_func


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


@imager_bp.route("/")
def index():
    return render_template("imager/index.html")


@imager_bp.route("/upload", methods=["GET", "POST"])
@login_required
@can_post_main_dashboard
def upload_images():
    upload_file_form = UploadFileForm()
    if upload_file_form.validate_on_submit():
        uploaded_file = upload_file_form.file.data
        filename = secure_filename(uploaded_file.filename)
        if filename != "":
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in current_app.config['UPLOAD_EXTENSIONS'] or \
                    file_ext != validate_image(uploaded_file.stream):
                flash("Invalid file type!")
                # abort(400)

            # Check if user has a folder for storing their content.
            # Create a folder for user if first time posting content.
            user_content = create_or_get_user_content(current_user)

            if not user_content:
                return SERVER_ERROR, 500

            image_details = {
                "name": request.form["name"]
            }

            status = save_user_image(
                current_user,
                uploaded_file,
                image_details)
            if not status:
                return SERVER_ERROR, 500

            flash("Image Successfully added.")
            return redirect(url_for('imager.index'))

    return render_template(
        "imager/upload.html",
        form=upload_file_form)


@imager_bp.route("/<string:image_id>")
def load_image(image_id):
    image_content = load_image_by_id(image_id)
    if image_content:
        # Folder path where user uploads will be.
        folder_path = os.path.join(
            current_app.config["UPLOAD_PATH"],
            image_content.user_content.content_location
        )

        # File regex for file name by ID.
        file_regex = os.path.join(
            folder_path,
            image_content.file_id + ".*")

        # Uses file_regex to get the proper filename with extension,
        # Assumes file extension is not stored on db so need to get
        # actual file with proper extension.
        image_file = [
            os.path.basename(fname) for fname in glob.glob(file_regex)]

        # Checks if actual file exists.
        if len(image_file) == 0:
            abort(404)
        # Check if duplicate files with same ID exists.
        elif len(image_file) > 1:
            # Log errors here, duplicates IDS not allowed.
            print("Duplicate file {} found".format(file_regex))
            abort(404)
        else:
            return send_from_directory(folder_path, image_file[0])

        return "Hello World"
    abort(404)
