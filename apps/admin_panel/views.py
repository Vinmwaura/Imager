from functools import wraps
from . import admin_panel_bp
from flask import (
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify)
from flask_login import login_required, current_user

from .. import auth, db
from sqlalchemy import asc

from .forms import RoleForm
from werkzeug import exceptions


def can_view_admin_dashboard():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_user.can_view_admin_dashboard():
                return fn(*args, **kwargs)
            else:
                return "You don't have permission to that"
        return decorator
    return wrapper


def can_insert_admin_dashboard():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_user.can_insert_admin_dashboard():
                return fn(*args, **kwargs)
            else:
                return "You don't have permission to that"
        return decorator
    return wrapper


def can_update_admin_dashboard():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_user.can_update_admin_dashboard():
                return fn(*args, **kwargs)
            else:
                return "You don't have permission to that"
        return decorator
    return wrapper


@admin_panel_bp.route("/")
@login_required
# @can_view_admin_dashboard()
def index():
    return render_template("admin_panel/admin_dashboard.html")


@admin_panel_bp.route("/view/users")
@login_required
# @can_view_admin_dashboard()
def view_users():
    users = auth.models.User.query.order_by(
        asc(auth.models.User.username))
    return render_template(
        "admin_panel/view_users.html",
        users=users)


@admin_panel_bp.route("/edit/user/<user_id>")
@login_required
def edit_user(user_id):
    user = auth.models.User.query.filter_by(
        id=user_id).first()
    return render_template(
        "admin_panel/deactivate_activate_user.html",
        user=user)


@admin_panel_bp.route("/deactivate/user/<user_id>")
@login_required
def deactivate_user(user_id):
    user_ = auth.models.User().query.filter_by(
        id=user_id).first()

    if user_.active:
        deactivation_status = user_.deactivate_user()
        if deactivation_status:
            flash("Successfully deactivated {}".format(
                user_.username))
        else:
            flash("An error occured while deactivating {}".format(
                user_.username))
    else:
        flash("{} has already been activated.".format(
            user_.username))
    return redirect(url_for("admin_panel.view_users"))


@admin_panel_bp.route("/activate/user/<user_id>")
@login_required
def activate_user(user_id):
    user_ = auth.models.User().query.filter_by(id=user_id).first()
    if not user_.active:
        activation_status = user_.activate_user()
        if activation_status:
            flash("Successfully activated {}".format(
                user_.username))
        else:
            flash("An error occured while activating {}".format(
                user_.username))
    else:
        flash("{} has already been activated.".format(
            user_.username))
    return redirect(url_for("admin_panel.view_users"))


@admin_panel_bp.route("/view/roles")
@login_required
# @can_view_admin_dashboard()
def view_roles():
    roles_list = []
    roles = auth.models.Role.query.order_by(
        asc(auth.models.Role.name))
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "permission_list": []}
        for permission_obj in role.permissions:
            role_dict["permission_list"].append(permission_obj.permission)
        roles_list.append(role_dict)
    permission_list = auth.models.PermissionsEnum
    return render_template(
        "admin_panel/view_roles.html",
        roles=roles_list,
        permissions=permission_list)


@admin_panel_bp.route("/add/role", methods=["GET", "POST"])
@login_required
# @can_view_admin_dashboard()
# @can_insert_admin_dashboard()
def add_role():
    permissions = auth.models.PermissionsEnum

    add_role_form = RoleForm()
    if add_role_form.validate_on_submit():
        # Check if role name has been used in database

        # Creates Role and Permission
        role_name = request.form["role_name"]
        role_added = auth.controllers.add_Role(
            role_name)

        try:
            db.session.commit()
        except Exception as e:
            print("An error occured while committing: {}".format(e))
            # Rollback session
            db.session.rollback()
            return render_template("admin_panel/add_role.html")

        for permission in permissions:
            try:
                permission_index = request.form[permission.name]
                _ = auth.controllers.add_Permission(
                    role_added.id,
                    permission_index)
            except exceptions.BadRequestKeyError as e:
                print(e)

        try:
            db.session.commit()
        except Exception as e:
            print("An error occured while committing: {}".format(e))
            # Rollback session
            db.session.rollback()
            return render_template("admin_panel/add_role.html")

        finally:
            flash("Successfully saved Roles and Permissions.")
            return redirect(url_for("admin_panel.index"))

    permission_list = auth.models.PermissionsEnum
    return render_template(
        "admin_panel/add_role.html",
        permissions=permission_list,
        form=add_role_form)


@admin_panel_bp.route("/edit/role/<role_id>", methods=["GET", "POST"])
@login_required
def edit_role(role_id):
    if role_id:
        role = auth.models.Role().query.filter_by(id=role_id).first()
        edit_role_form = RoleForm(
            role_name=role.name)

        role_permissions = auth.models.Permissions().query.filter_by(
            role_id=role_id).all()
        all_permissions = auth.models.PermissionsEnum

        active_permissions = []
        for permision in role_permissions:
            active_permissions.append(permision.permission)

        if edit_role_form.validate_on_submit():
            role.name = request.form["role_name"]

            db.session.add(role)

            for permission in all_permissions:
                role_perm = auth.models.Permissions().query.filter_by(
                    role_id=role_id, permission=permission.value).all()
                # If permission exists in table
                if role_perm:
                    # Check if permission has not been checked on form
                    if permission.name not in request.form:
                        auth.models.Permissions().query.filter_by(
                            role_id=role_id,
                            permission=permission.value).delete()
                else:
                    # Check if permission has been checked on form
                    if permission.name in request.form:
                        # Adds permission to permissions table
                        _ = auth.controllers.add_Permission(
                            role_id,
                            permission.value)
            try:
                db.session.commit()
                return redirect(url_for("admin_panel.view_roles"))
            except Exception as e:
                db.session.rollback()
                flash("An erro occurred while saving data")
                print(
                    "An exception occured while commiting Role updates", e)

        return render_template(
            "admin_panel/edit_role.html",
            permissions=all_permissions,
            active_permissions=active_permissions,
            role_id=role_id,
            form=edit_role_form)
    else:
        return "No or invalid parameter passed."
