import os
import imghdr
import uuid


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


def create_content_directory(file_path, directory_name=None):
    if not directory_name or not isinstance(directory_name, str):
        # Generates a random unique id for each user's directory
        directory_name = uuid.uuid4().hex
    try:
        os.makedirs(
            os.path.join(
                file_path,
                str(directory_name))
        )
    except Exception as e:
        print("An error occured while making user directory: ", e)

    return os.path.isdir(
        os.path.join(
            file_path,
            str(directory_name))), directory_name


def generate_filename(name_len=8):
    file_name = "%s" % os.urandom(8).hex()
    return file_name
