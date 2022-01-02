from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from .. import auth, db


def get_all_permission_enums():
    # Gets all permissions enum.
    all_permission = auth.models.PermissionsEnum
    return all_permission


def get_all_users():
    users = auth.models.User.query.order_by(
        auth.models.User.username.asc()).all()
    return users


def get_all_roles():
    roles = auth.models.Role.query.order_by(
        auth.models.Role.id.desc()).all()
    return roles


def load_user_by_id(user_id):
    # Filter by specific user id.
    user = auth.models.User.query.filter_by(
        id=user_id).one_or_none()
    return user


def load_user_by_role_id(role_id):
    # Filter by specific user id.
    users = auth.models.User().query.filter_by(
        user_role=role_id).all()
    return users


def load_role_by_id(role_id):
    role = auth.models.Role().query.filter_by(
        id=role_id).one_or_none()
    return role


def load_permissions_by_role_id(role_id):
    role_permissions = auth.models.Permissions().query.filter_by(
        role_id=role_id).all()
    return role_permissions


def load_specific_permissions_by_role_id(role_id, permission_value):
    print(role_id, permission_value)
    # Gets Permission for Role if it exists.
    role_perm = auth.models.Permissions().query.filter_by(
        role_id=role_id,
        permission=permission_value).one_or_none()
    return role_perm


def update_user_role(user, role):
    try:
        # Update user role.
        user.user_role = role
        # Commit Session
        db.session.commit()
        return True
    except Exception as e:
        # Rollback session
        db.session.rollback()
        print("An error occured while updating user role: ", e)
        return False


def update_role(role, role_name):
    # Attempt to update Role with new name
    try:
        role.name = role_name

        # Commit Session
        db.session.commit()
        return True, None
    except IntegrityError as e:
        # Rollback Session
        db.session.rollback()
        # Catches duplicate errors when they occur
        if isinstance(e.orig, UniqueViolation):
            # flash(DUPLICATE_ERROR(role_name, "Role"), "error")
            return False, "duplicate"
        else:
            # Catches other errors when they occur
            print("An error occured while updating Role: ", e)
            # flash(SERVER_ERROR, "error")
            return False, "server"
    except Exception as e:
        # Rollback session
        db.session.rollback()
        print("An error occured while updating role: ", e)
        return False, "server"


def add_role_name(role_name):
    # Adds Role to database.
    role_added = auth.controllers.add_Role(
        role_name)

    if role_added:
        try:
            # Commit Session
            db.session.commit()
            return role_added, None
        except IntegrityError as e:
            # Rollback Session
            db.session.rollback()

            # Catches duplicate errors when they occur
            if isinstance(e.orig, UniqueViolation):
                # flash(DUPLICATE_ERROR(role_name, "Role"), "error")
                return None, "duplicate"
            else:
                # Catches other errors when they occur
                print("An error occured while adding Role name: ", e)
                # flash(SERVER_ERROR, "error")
                return None, "server"
        except Exception as e:
            # Rollback session
            db.session.rollback()
            print("An error occured while adding Role name: ", e)
            # flash(SERVER_ERROR, "error")
            return None, "server"
    else:
        # flash(SERVER_ERROR, "error")
        return None, "server"


def add_permission(all_permissions, request_form, role_added):
    for permission in all_permissions:
        # If permission has been checked on form, add
        if permission.name in request_form:
            permission_index = request_form[permission.name]
            permission_added = auth.controllers.add_Permission(
                role_added.id,
                permission_index)

            if not permission_added:
                # Rollback session
                db.session.rollback()
                print("An error occured while adding permission!")
                return False

    try:
        db.session.commit()
        return True
    except Exception as e:
        # Rollback session
        db.session.rollback()
        print("An error occured while adding permission: {}".format(e))
        return False


def delete_permission_and_role(role_id):
    # Deletes Permissions for that Role
    auth.models.Permissions().query.filter_by(
        role_id=role_id).delete()

    # Deletes Role
    auth.models.Role().query.filter_by(id=role_id).delete()

    try:
        # Session Commit
        db.session.commit()
        return True
    except Exception as e:
        print("An error occured deleting permission and role: ", e)
        db.session.rollback()
        return False


def delete_role_permision(role_id, permission_value):
    try:
        # Deletes permission from table.
        auth.models.Permissions().query.filter_by(
            role_id=role_id,
            permission=permission_value).delete()
        return True
    except Exception as e:
        print("An error occured deleting permission: ", e)
        return False


def remove_unselected_permissions(
    role_id,
    request_form,
    all_permissions):
    for permission in all_permissions:
        role_perm = load_specific_permissions_by_role_id(
            role_id,
            permission.value)

        # If permission exists in table.
        if role_perm:
            # Check if permission has not been checked on form.
            if permission.name not in request_form:
                _ = delete_role_permision(
                    role_id, permission.value)
        else:
            # Check if permission has been checked on form.
            if permission.name in request_form:
                # Adds permission to table.
                _ = auth.controllers.add_Permission(
                    role_id,
                    permission.value)

    # Try and commit delete Roles and Permissions.
    try:
        # Session Commit.
        db.session.commit()
        return True
    except Exception as e:
        # Session Rollback.
        db.session.rollback()
        print(
            "An exception occured while commiting: ", e)
        return False
