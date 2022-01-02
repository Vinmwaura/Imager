from functools import wraps

from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request)

from flask_login import (
    login_required,
    current_user)

from .forms import RoleForm, UserForm

from . import admin_panel_bp
from .controllers import *
from .utils import *


# Decorators to manage authorization of users
def can_view_admin_dashboard(func):
    @login_required
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_view_admin_dashboard() and \
                current_user.is_active():
            return func(*args, **kwargs)
        else:
            return ACCESS_DENIED, 403
    return inner_func


# Assumes you can view admin dashboard to insert
def can_insert_admin_dashboard(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_insert_admin_dashboard():
            return func(*args, **kwargs)
        else:
            return ACCESS_DENIED, 403
    return inner_func


# Assumes you can view admin dashboard to update
def can_update_admin_dashboard(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_update_admin_dashboard():
            return func(*args, **kwargs)
        else:
            return ACCESS_DENIED, 403
    return inner_func


# Assumes you can view admin dashboard to delete
def can_delete_admin_dashboard(func):
    @wraps(func)
    def inner_func(*args, **kwargs):
        if current_user.can_delete_admin_dashboard():
            return func(*args, **kwargs)
        else:
            return ACCESS_DENIED, 403
    return inner_func


@admin_panel_bp.route("/")
@can_view_admin_dashboard
def index():
    return render_template(
        "admin_panel/admin_dashboard.html")


@admin_panel_bp.route("/view/users")
@can_view_admin_dashboard
def view_users():
    users = get_all_users()
    return render_template(
        "admin_panel/view_users.html",
        users=users)


@admin_panel_bp.route("/edit/user/role/<int:user_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_user_role(user_id):
    # Filter by specific user id
    user = load_user_by_id(user_id)
    if user:
        # Prepopulate user form with user details
        edit_user_form = UserForm(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.user_role)

        # Prepopulate Role with all Roles currently created.
        edit_user_form.role.choices = [
            (role.id, role.name) for role in get_all_roles()]
        if edit_user_form.validate_on_submit():
            role_id = request.form["role"]
            if role_id:
                update_status = update_user_role(user, role_id)
                if update_status:
                    flash(ROLE_UPDATE_SUCCESS(user.username), "success")
                    return redirect(
                        url_for(
                            'admin_panel.view_users'
                        ))
                else:
                    flash(SERVER_ERROR, "error")
            else:
                flash(
                    ROLE_UPDATE_ERROR,
                    "error")
        return render_template(
            "admin_panel/edit_user.html",
            user=user,
            form=edit_user_form)
    else:
        flash(DATA_NOT_FOUND, "error")
        return redirect(url_for('admin_panel.view_users'))


@admin_panel_bp.route(
    "/edit/user/status/<int:user_id>",
    methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_user_status(user_id):
    # Filter by specific user id
    user = load_user_by_id(user_id)
    if user:
        # Prepopulate user form with user details
        deactivate_user_form = UserForm(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.user_role)

        # Prepopulate Role with all Roles currently created.
        deactivate_user_form.role.choices = [
            (role.id, role.name) for role in get_all_roles()]

        if deactivate_user_form.validate_on_submit():
            if user.active:
                deactivation_status = user.deactivate_user()
                if deactivation_status:
                    flash(SUCCESS_DEACTIVATE_USER(user.username), "success")
                else:
                    flash(ERROR_DEACTIVATE_USER(user.username), "error")
            else:
                activation_status = user.activate_user()
                if activation_status:
                    flash(SUCCESS_ACTIVATE_USER(user.username), "success")
                else:
                    flash(ERROR_ACTIVATE_USER(user.username), "error")
            return redirect(url_for('admin_panel.view_users'))

        return render_template(
            "admin_panel/deactivate_activate_user.html",
            user=user,
            form=deactivate_user_form)
    else:
        flash(DATA_NOT_FOUND, "error")
        return redirect(url_for('admin_panel.view_users'))


@admin_panel_bp.route("/view/roles")
@can_view_admin_dashboard
def view_roles():
    roles_list = []
    roles = get_all_roles()

    # Combines all Roles and Permissions in a dict
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "permission_list": []}
        for permission_obj in role.permissions:
            role_dict["permission_list"].append(permission_obj.permission)
        roles_list.append(role_dict)

    # Gets all permissions enum
    all_permission = get_all_permission_enums()

    return render_template(
        "admin_panel/view_roles.html",
        roles=roles_list,
        permissions=all_permission)


@admin_panel_bp.route("/add/role", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_insert_admin_dashboard
def add_role():
    # Gets all permissions enum.
    all_permissions = get_all_permission_enums()

    # Add Role Form.
    add_role_form = RoleForm()
    if add_role_form.validate_on_submit():
        # Adds new role to Role table.
        role_name = request.form["role_name"]
        role_added, error_type = add_role_name(role_name)

        if role_added is not None:
            flash(
                SUCCESS_ADD_ROLE(role_name), "success")

            permission_status = add_permission(
                all_permissions,
                request.form,
                role_added)

            if permission_status:
                flash(SUCCESS_ADD_PERMISSION, "success")
            else:
                flash(ERROR_ADD_PERMISSION, "error")

        else:
            if error_type == "duplicate":
                flash(DUPLICATE_ERROR(role_name, "Role"), "error")
            elif error_type == "server":
                flash(SERVER_ERROR, "error")
            else:
                flash(SERVER_ERROR, "error")

        return redirect(
            url_for('admin_panel.view_roles'))
    return render_template(
        "admin_panel/add_role.html",
        permissions=all_permissions,
        form=add_role_form)


@admin_panel_bp.route("/edit/role/<int:role_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_role(role_id):
    role = load_role_by_id(role_id)
    if role:
        all_permissions = get_all_permission_enums()

        role_permissions = load_permissions_by_role_id(role_id)

        active_permissions = []
        for permision in role_permissions:
            active_permissions.append(permision.permission)

        edit_role_form = RoleForm(
            role_name=role.name)
        if edit_role_form.validate_on_submit():
            role_name = request.form["role_name"]

            role_updated, error_type = update_role(role, role_name)
            if role_updated:
                flash(
                    ROLE_UPDATE_SUCCESS(role_name),
                    "success")

                del_status = remove_unselected_permissions(
                    role.id,
                    request.form,
                    all_permissions)

                if del_status:
                    flash(SUCCESS_UPDATE_PERMISSION, "success")
                else:
                    flash(ERROR_UPDATE_PERMISSION, "error")

            else:
                if error_type == "duplicate":
                    flash(DUPLICATE_ERROR(role_name, "Role"), "error")
                elif error_type == "server":
                    flash(SERVER_ERROR, "error")
                else:
                    flash(SERVER_ERROR, "error")

            return redirect(url_for("admin_panel.view_roles"))

        return render_template(
            "admin_panel/edit_role.html",
            permissions=all_permissions,
            active_permissions=active_permissions,
            role_id=role_id,
            form=edit_role_form)
    else:
        flash(DATA_NOT_FOUND, "error")
        return redirect(url_for('admin_panel.view_roles'))


@admin_panel_bp.route("/delete/role/<int:role_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_delete_admin_dashboard
def delete_role(role_id):
    role = load_role_by_id(role_id)
    if role:
        all_permissions = get_all_permission_enums()
        role_permissions = load_permissions_by_role_id(role_id)

        active_permissions = []
        for permision in role_permissions:
            active_permissions.append(permision.permission)

        # Delete Form.
        delete_role_form = RoleForm(
            role_name=role.name)

        if delete_role_form.validate_on_submit():
            # Check if there's any User who has role.
            users = load_user_by_role_id(role_id)

            if users:
                flash(ERROR_DEL_ROLE_FAILED_USER(users), "info")
            else:
                role_name = role.name

                del_status = delete_permission_and_role(role_id)
                if del_status:
                    flash(SUCCESS_DEL_ROLE(role_name), "success")
                else:
                    flash(ERROR_DEL_ROLE, "error")
            return redirect(url_for('admin_panel.view_roles'))
    else:
        flash(DATA_NOT_FOUND, "error")
        return redirect(url_for('admin_panel.view_roles'))

    return render_template(
        "admin_panel/delete_role.html",
        permissions=all_permissions,
        active_permissions=active_permissions,
        role_id=role_id,
        form=delete_role_form)
