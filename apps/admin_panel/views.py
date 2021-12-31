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
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from . import admin_panel_bp
from .. import auth, db
from .forms import RoleForm, UserForm


ACCESS_DENIED = "You don't have permission to view this page,"\
    " Contact Administrator if you think you should."
SERVER_ERROR = "An error occured in the server, while processing the request."
DATA_NOT_FOUND = "No data found."
DUPLICATE_ERROR = lambda field_name, table_name: "{} has already been "\
    "used in {}.".format(
        field_name,
        table_name)


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


@admin_panel_bp.route("/")
@can_view_admin_dashboard
def index():
    return render_template(
        "admin_panel/admin_dashboard.html")


@admin_panel_bp.route("/view/users")
@can_view_admin_dashboard
def view_users():
    users = auth.models.User.query.all()
    return render_template(
        "admin_panel/view_users.html",
        users=users)


@admin_panel_bp.route("/edit/user/role/<int:user_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_user_role(user_id):
    # Filter by specific user id
    user = auth.models.User.query.filter_by(
        id=user_id).first()
    if user:
        # Prepopulate user form with user details
        edit_user_form = UserForm(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.user_role)

        # Prepopulate Role with all Roles currently created
        edit_user_form.role.choices = [
            (role.id, role.name) for role in auth.models.Role.query.all()]

        if edit_user_form.validate_on_submit():
            role_id = request.form["role"]
            user.user_role = role_id

            try:
                # Commit Session
                db.session.commit()
                flash(
                    "Successfully updated {}'s Role!".format(
                        user.username), "success")
                return redirect(
                    url_for(
                        'admin_panel.view_users'
                    ))
            except Exception as e:
                # Rollback session
                db.session.rollback()
                print("An error occured while commiting Role: ", e)
                flash(SERVER_ERROR, "error")

        return render_template(
            "admin_panel/edit_user.html",
            user=user,
            form=edit_user_form)
    return DATA_NOT_FOUND


@admin_panel_bp.route("/edit/user/status/<int:user_id>")
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_user_status(user_id):
    user = auth.models.User.query.filter_by(
        id=user_id).first()
    if user:
        return render_template(
            "admin_panel/deactivate_activate_user.html",
            user=user)
    else:
        return DATA_NOT_FOUND


@admin_panel_bp.route("/activate/user/<int:user_id>")
@can_view_admin_dashboard
@can_update_admin_dashboard
def activate_user(user_id):
    user_ = auth.models.User().query.filter_by(id=user_id).first()
    if user_:
        if not user_.active:
            activation_status = user_.activate_user()
            if activation_status:
                flash("Successfully activated {}".format(
                    user_.username), "success")
            else:
                flash("An error occured while activating {}".format(
                    user_.username))
        else:
            flash("{} has already been activated.".format(
                user_.username), "info")
        return redirect(url_for("admin_panel.view_users"))
    else:
        return DATA_NOT_FOUND


@admin_panel_bp.route("/deactivate/user/<int:user_id>")
@can_view_admin_dashboard
@can_update_admin_dashboard
def deactivate_user(user_id):
    user_ = auth.models.User().query.filter_by(
        id=user_id).first()
    if user_:
        if user_.active:
            deactivation_status = user_.deactivate_user()
            if deactivation_status:
                flash("Successfully deactivated {}".format(
                    user_.username), "success")
            else:
                flash("An error occured while deactivating {}".format(
                    user_.username), "error")
        else:
            flash("{} has already been deactivated.".format(
                user_.username), "info")
        return redirect(url_for("admin_panel.view_users"))
    else:
        return DATA_NOT_FOUND


@admin_panel_bp.route("/view/roles")
@can_view_admin_dashboard
def view_roles():
    roles_list = []
    roles = auth.models.Role.query.all()

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
    all_permission = auth.models.PermissionsEnum

    return render_template(
        "admin_panel/view_roles.html",
        roles=roles_list,
        permissions=all_permission)


@admin_panel_bp.route("/add/role", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_insert_admin_dashboard
def add_role():
    # Gets all permissions enum
    all_permissions = auth.models.PermissionsEnum

    add_role_form = RoleForm()

    if add_role_form.validate_on_submit():
        # Adds Role to database
        role_name = request.form["role_name"]
        role_added = auth.controllers.add_Role(
            role_name)

        role_commited_status = False

        if role_added:
            try:
                # Commit Session
                db.session.commit()
                flash(
                    "Successfully added {} Role!".format(
                        role_name), "success")
                role_commited_status = True
            except IntegrityError as e:
                # Rollback Session
                db.session.rollback()

                # Catches duplicate errors when they occur
                if isinstance(e.orig, UniqueViolation):
                    flash(DUPLICATE_ERROR(role_name, "Role"), "error")
                else:
                    # Catches other errors when they occur
                    print("An error occured while commiting Role: ", e)
                    flash(SERVER_ERROR, "error")
            except Exception as e:
                # Rollback session
                db.session.rollback()
                print("An error occured while commiting Role: ", e)
                flash(SERVER_ERROR, "error")
        else:
            flash(SERVER_ERROR, "error")

        # Adds Permission for Role in database if Role was
        # successfully commited
        cancelled_status = False
        if role_commited_status:
            for permission in all_permissions:
                # If permission has been checked on form, add
                if permission.name in request.form:
                    permission_index = request.form[permission.name]
                    permission_added = auth.controllers.add_Permission(
                        role_added.id,
                        permission_index)

                    if not permission_added:
                        # Rollback session
                        db.session.rollback()
                        print("An error occured while adding permission!")
                        cancelled_status = True
                        break
            if not cancelled_status:
                try:
                    db.session.commit()
                    flash("Successfully added Permissions!", "success")
                except Exception as e:
                    # Rollback session
                    db.session.rollback()
                    print("An error occured while committing: {}".format(e))
        return redirect(
            url_for('admin_panel.add_role'))
    return render_template(
        "admin_panel/add_role.html",
        permissions=all_permissions,
        form=add_role_form)


@admin_panel_bp.route("/edit/role/<int:role_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def edit_role(role_id):
    role = auth.models.Role().query.filter_by(id=role_id).first()
    if role:
        all_permissions = auth.models.PermissionsEnum

        role_permissions = auth.models.Permissions().query.filter_by(
            role_id=role_id).all()

        active_permissions = []
        for permision in role_permissions:
            active_permissions.append(permision.permission)

        edit_role_form = RoleForm(
            role_name=role.name)
        if edit_role_form.validate_on_submit():
            role_name = request.form["role_name"]
            role.name = role_name

            role_commited_status = False
            # Attempt to update Role with new name
            try:
                # Commit Session
                db.session.commit()
                flash(
                    "Successfully updated {} Role!".format(
                        role_name), "success")
                role_commited_status = True
            except IntegrityError as e:
                # Rollback Session
                db.session.rollback()

                # Catches duplicate errors when they occur
                if isinstance(e.orig, UniqueViolation):
                    flash(DUPLICATE_ERROR(role_name, "Role"), "error")
                else:
                    # Catches other errors when they occur
                    print("An error occured while commiting Role: ", e)
                    flash(SERVER_ERROR, "error")
            except Exception as e:
                # Rollback session
                db.session.rollback()
                print("An error occured while commiting Role: ", e)
                flash(SERVER_ERROR, "error")

            if role_commited_status:
                for permission in all_permissions:
                    # Gets Permission for Role if it exists.
                    role_perm = auth.models.Permissions().query.filter_by(
                        role_id=role_id,
                        permission=permission.value).first()

                    # If permission exists in table.
                    if role_perm:
                        # Check if permission has not been checked on form.
                        if permission.name not in request.form:
                            # Deletes permission from table.
                            auth.models.Permissions().query.filter_by(
                                role_id=role_id,
                                permission=permission.value).delete()
                    else:
                        # Check if permission has been checked on form
                        if permission.name in request.form:
                            # Adds permission to table.
                            _ = auth.controllers.add_Permission(
                                role_id,
                                permission.value)

                try:
                    # Session Commit
                    db.session.commit()
                    flash("Successfully updated Permissions!", "success")
                except Exception as e:
                    db.session.rollback()
                    flash("An error occurred while updating Permissions", "error")
                    print(
                        "An exception occured while commiting Role updates", e)
            return redirect(url_for("admin_panel.view_roles"))

        return render_template(
            "admin_panel/edit_role.html",
            permissions=all_permissions,
            active_permissions=active_permissions,
            role_id=role_id,
            form=edit_role_form)
    else:
        return DATA_NOT_FOUND


@admin_panel_bp.route("/delete/role/<int:role_id>", methods=["GET", "POST"])
@can_view_admin_dashboard
@can_update_admin_dashboard
def delete_role(role_id):
    role = auth.models.Role().query.filter_by(id=role_id).first()
    if role:
        all_permissions = auth.models.PermissionsEnum
        role_permissions = auth.models.Permissions().query.filter_by(
            role_id=role_id).all()

        active_permissions = []
        for permision in role_permissions:
            active_permissions.append(permision.permission)

        delete_role_form = RoleForm(
            role_name=role.name)

        if delete_role_form.validate_on_submit():
            # Check if there's any User who has role
            users = auth.models.User().query.filter_by(user_role=role_id).all()

            if users:
                message = "{} Users found, with that role. Kindly change the "\
                    "users role to be able to delete this.".format(
                        len(users))
                flash(message, "info")
            else:
                role_names = role.name
                # Deletes Permissions for that Role
                auth.models.Permissions().query.filter_by(
                    role_id=role_id).delete()
                # Deletes Role
                auth.models.Role().query.filter_by(id=role_id).delete()

                try:
                    # Session Commit
                    db.session.commit()
                    flash("Successfully deleted Role: {}".format(role_names), "success")
                    return redirect(
                        url_for(
                            "admin_panel.view_roles"))
                except Exception as e:
                    db.session.rollback()
                    flash("An error occurred while deleting Role", "error")
                    print(
                        "An exception occured while deleting Role", e)
    else:
        return DATA_NOT_FOUND

    return render_template(
        "admin_panel/delete_role.html",
        permissions=all_permissions,
        active_permissions=active_permissions,
        role_id=role_id,
        form=delete_role_form)
