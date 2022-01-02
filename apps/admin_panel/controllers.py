from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from .. import auth, db


def get_all_permission_enums():
    """
    Gets all Permissions Enums.

    Returns:
      Returns list of all Permissions Enums.
    """
    all_permission = auth.models.PermissionsEnum
    return all_permission


def get_all_users():
    """
    Gets a list of all Users.

    Returns:
      List of all Users in database.
    """
    users = auth.models.User.query.order_by(
        auth.models.User.username.asc()).all()
    return users


def get_all_roles():
    """
    Gets a list of all Roles.

    Returns:
      List of all Roles in database.
    """
    roles = auth.models.Role.query.order_by(
        auth.models.Role.id.desc()).all()
    return roles


def load_user_by_id(user_id):
    """
    Gets specific User filtered by ID.

    Args:
      user_id: User ID.

    Returns:
      User object.
    """
    # Filter by specific user id.
    user = auth.models.User.query.filter_by(
        id=user_id).one_or_none()
    return user


def load_user_by_role_id(role_id):
    """
    Gets Users filtered by Role assigned to them.

    Args:
      role_id: Role ID.

    Returns:
      List of all Users filtered by Roles in database.
    """
    # Filter by specific user id.
    users = auth.models.User().query.filter_by(
        user_role=role_id).all()
    return users


def load_role_by_id(role_id):
    """
    Gets Role filtered by ID.

    Args:
      role_id: Role ID.

    Returns:
      Role object.
    """
    role = auth.models.Role().query.filter_by(
        id=role_id).one_or_none()
    return role


def load_permissions_by_role_id(role_id):
    """
    Gets Permissions filtered by Role ID.

    Args:
      role_id: Role ID.

    Returns:
      List of Permission filtered by Role.
    """
    role_permissions = auth.models.Permissions().query.filter_by(
        role_id=role_id).all()
    return role_permissions


def load_specific_permissions_by_role_id(role_id, permission_value):
    """
    Gets specific Permission filtered by Role ID and value.

    Args:
      role_id: Role ID.
      permission_value: Permission ID value.

    Returns:
      Permission Object filtered by Role and permission value.
    """
    # Gets Permission for Role if it exists.
    role_perm = auth.models.Permissions().query.filter_by(
        role_id=role_id,
        permission=permission_value).one_or_none()
    return role_perm


def update_user_role(user, role_id):
    """
    Update User's Role.

    Args:
      user: User object.
      role_id: Role ID.

    Returns:
      Boolean indicating status of operation.
    """
    try:
        # Update user role.
        user.user_role = role_id

        # Commit Session
        db.session.commit()
        return True
    except Exception as e:
        # Rollback session
        db.session.rollback()
        print("An error occured while updating user role: ", e)
        return False


def update_role(role, role_name):
    """
    Update Role.

    Args:
      role: Role object.
      role_name: New Role name.

    Returns:
      Tuple with boolean indicating status of operation and error type.
    """
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
    """
    Adds Role to database.

    Args:
      role_name: Role name.

    Returns:
      Tuple with boolean indicating status of operation and error type.
    """
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
    """
    Adds Permission to database.

    Args:
      all_permissions: List of all permissions.
      request_form: Form results containing permissions selected.
      role_added: Role Object.

    Returns:
      Boolean indicating status of operation.
    """
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
    """
    Deletes Role and it's Permissions based on Role ID.

    Args:
      role_id: Role ID.

    Returns:
      Boolean indicating status of operation.
    """
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
    """
    Deletes Specific Permision for a Role in the case of Role .

    Args:
      role_id: Role ID.
      permission_value: Permission ID value.

    Returns:
      Boolean indicating status of operation.
    """
    try:
        # Deletes permission from table.
        auth.models.Permissions().query.filter_by(
            role_id=role_id,
            permission=permission_value).delete()
        return True
    except Exception as e:
        print("An error occured deleting permission: ", e)
        return False


def update_permissions(
        role_id, request_form, all_permissions):
    """
    Updates Permisions for a Role in the case of updates.

    Args:
      role_id: Role ID.
      request_form: Form results containing permissions selected.
      all_permissions: List of all permissions.

    Returns:
      Boolean indicating status of operation.
    """
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
