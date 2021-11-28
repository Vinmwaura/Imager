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


def create_content_directory(file_path):
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


def generate_filename(user_id, file_ext, name_len=8):
    file_name = "%s_%s.%s" % (
        user_id,
        os.urandom(8).hex(),
        file_ext)
    return file_name
