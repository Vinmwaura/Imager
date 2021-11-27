from flask import render_template

from . import imager_bp


@imager_bp.route("/")
def index():
    return render_template("imager/index.html")
