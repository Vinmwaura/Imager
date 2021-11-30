import os
import imghdr
import uuid


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
    return '.' + (format if format != 'jpeg' else 'jpg')


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
