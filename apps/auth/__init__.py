from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

from . import views
from . import models
from . import controllers
