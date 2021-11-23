from flask import Blueprint

admin_panel_bp = Blueprint("admin_panel", __name__, url_prefix="/admin")

from . import views
