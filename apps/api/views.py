from flask import (
    jsonify,
    url_for,
    request)

from . import api_bp
from .controllers import *


@api_bp.route("/api/v1/gallery/")
@api_bp.route("/api/v1/gallery/<string:category>")
@api_bp.route("/api/v1/gallery/<string:category>/<string:category_filter>")
def load_gallery(category="upload_time", category_filter=None):
    # Assumes no issue will occur otherwise will be changed.
    message = "Successful."
    api_status = 200

    if category == "upload_time":
        if category_filter is None:
            category_filter = "desc"  # Default value if no parameter passed.
        image_contents = get_image_contents_by_time(category_filter)
    elif category == "score":
        if category_filter is None:
            category_filter = "desc"  # Default value if no parameter passed.
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
