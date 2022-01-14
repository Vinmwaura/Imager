import os
import glob
import uuid
import imghdr
from functools import wraps
from flask_login import current_user


PERMISSION_DENIED = "You don't have permission to post to this page,"\
    " Contact Administrator if you think you should."
SERVER_ERROR = "An error occured in the server."

MIN_TITLE_LENGTH = 1
MAX_TITLE_LENGTH = 20
INVALID_TITLE_LENGTH = "Title must be between {} and {} characters.".format(
    MIN_TITLE_LENGTH, MAX_TITLE_LENGTH)

EMAIL_CHANGE_WARNING = "Changing Email will require a new activation \
            link to be sent to the new email provided, kindly ensure \
            it's valid before saving as you won't be able to login next \
            time without confirming email."
USERNAME_SUCCESSFULLY_CHANGED = "Successfully changed username."
FIRSTNAME_SUCCESSFULLY_CHANGED = "Successfully changed first_name."
LASTNAME_SUCCESSFULLY_CHANGED = "Successfully changed last_name."
EMAIL_SUCCESSFULLY_CHANGED = "Successfully changed email."

USERNAME_FAILED_CHANGED = "An error occured while changing username."
FIRSTNAME_FAILED_CHANGED = "An error occured while changing first_name."
LASTNAME_FAILED_CHANGED = "An error occured while changing last_name."
EMAIL_FAILED_CHANGED = "An error occured while changing email."

EMAIL_SUCCESSFULLY_SENT = "Confirmation Email has been sent to the new email."
EMAIL_FAILED_SENT = "An error occured sending email."


# Assumes you can view main dashboard to post
def can_post_main_dashboard(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_post_main_dashboard():
            return func(*args, **kwargs)
        else:
            return PERMISSION_DENIED, 403
    return inner_func


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


def validate_image(stream):
    """
    Validates image using stream data.

    Args:
      stream: Image stream.

    Returns:
      None or image extension.
    """
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format


def create_content_directory(file_path, directory_name=None):
    """
    Creates directory for user uploads including thumbnail directory.

    Args:
      file_path: Path where directory will be stored.
      directory_name: Specific directory name to be used.

    Returns:
      Tuple containing boolean directory was created and name of directory.
    """
    if not directory_name or not isinstance(directory_name, str):
        # Generates a random unique id for each user's directory.
        directory_name = uuid.uuid4().hex

    # User upload directory
    user_upload_directory = os.path.join(
        file_path,
        str(directory_name))

    # Directory for storing each user's image thumbnails.
    thumbnail_directory = os.path.join(
        user_upload_directory,
        'thumbnails')
    try:
        # os.makedirs(user_upload_directory)
        os.makedirs(thumbnail_directory)
    except Exception as e:
        print("An error occured while making user directory: ", e)
        # Remove directory if any error occurs during creating directory.
        if os.path.isdir(user_upload_directory):
            os.removedirs(user_upload_directory)

    # If thumbnail directory exists, assume everything was ok.
    return os.path.isdir(thumbnail_directory), directory_name


def generate_filename(name_len=8):
    """
    Generates random hex string for filenames.

    Args:
      name_len: Size in bytes of the filename.

    Returns:
      Randomly created filename string.
    """
    file_name = "%s" % os.urandom(8).hex()
    return file_name


def get_image_file_paths(image_content, upload_path):
    """
    Get file path for images based on ImageContent object from db.

    Args:
      image_content: ImageContent object containing fileid and directory id.
      upload_path: File path where user uploads directory is located
                    on the server.

    Returns:
      List of filepaths of the images.
    """
    # Folder path where user uploads will be.
    folder_path = os.path.join(
        upload_path,
        image_content.user_content.content_location
    )

    # File regex for file name by ID.
    file_regex = os.path.join(
        folder_path,
        image_content.file_id + ".*")

    # Uses file_regex to get the proper filename with extension,
    # Assumes file extension is not stored on db so need to get
    # actual file with proper extension.
    image_filenames = [
        os.path.basename(fname) for fname in glob.glob(file_regex)]
    return folder_path, image_filenames


def delete_image_file(file_path, directory_name, file_id):
    """
    Removes images and thumbnail image in their respective folder.

    Args:
      file_path: File path where images are stored.
      directory_name: Directory name of the user content.
      file_id: File name.

    Returns:
      Boolean indicating result of operation.
    """

    # Directory Path of user content.
    dir_path = os.path.join(file_path, directory_name)

    # Check if folder exists, and if return False.
    is_dir = os.path.isdir(dir_path)
    if not is_dir:
        return False

    # Image file regex.
    file_regex = os.path.join(dir_path, file_id + ".*")
    image_del_list = glob.glob(file_regex)

    # Thumbnail file regex.
    thumbnail_regex = os.path.join(*[dir_path, 'thumbnails', file_id + ".*"])
    image_del_list += glob.glob(thumbnail_regex)

    try:
        # Remove image file and thumbnail from location.
        for image in image_del_list:
            os.remove(image)

        return True

    except Exception as e:
        # TODO: Log error messages properly to a file.
        print("An error occured while removing files in the server: ", e)
        return False
