from .models import PermissionsEnum

# Default Role Names
DEFAULT_ADMIN_ROLE = "ADMIN"
DEFAULT_GENERAL_USER_ROLE = "GENERAL"

# List of permissions Anonymous user permission
GUEST_PERMISSION_LIST = [
    PermissionsEnum.CAN_VIEW_DASHBOARD
]

# List of permissions General Users should have
GENERAL_USER_PERMISSIONS = [
    PermissionsEnum.CAN_POST_DASHBOARD,
    PermissionsEnum.CAN_VIEW_DASHBOARD
]

# List of permissions Admin should have
ADMIN_PERMISSION_LIST = [
    PermissionsEnum.CAN_VIEW_ADMIN,
    PermissionsEnum.CAN_UPDATE_ADMIN,
    PermissionsEnum.CAN_INSERT_ADMIN,
    PermissionsEnum.CAN_POST_DASHBOARD,
    PermissionsEnum.CAN_VIEW_DASHBOARD,
    PermissionsEnum.CAN_DELETE_ADMIN
]
