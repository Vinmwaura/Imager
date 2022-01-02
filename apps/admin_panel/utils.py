ACCESS_DENIED = "You don't have permission to view this page,"\
    " Contact Administrator if you think you should."
SERVER_ERROR = "An error occured in the server, while processing the request."
ROLE_UPDATE_ERROR = "Server error occured and user role couldn't be updated."
DATA_NOT_FOUND = "No data found."
SUCCESS_ADD_PERMISSION = "Successfully added Permissions!"
ERROR_ADD_PERMISSION = "Error occured adding permissions!"

SUCCESS_UPDATE_PERMISSION = "Successfully updated Permissions!"
ERROR_UPDATE_PERMISSION = "An error occurred while updating Permissions!"

SUCCESS_ACTIVATE_USER = lambda username: "Successfully activated {}!".format(
    username)
ERROR_ACTIVATE_USER = lambda username: "An error occured while activating {}!".format(
    username)

SUCCESS_DEACTIVATE_USER = lambda username: "Successfully deactivated {}!".format(
    username)
ERROR_DEACTIVATE_USER = lambda username: "An error occured while deactivating {}!".format(
    username)

ERROR_DEL_ROLE_FAILED_USER = lambda users: "{} Users found, with that role."\
    " Kindly change the users role to be able to delete this.".format(
        len(users))

SUCCESS_ADD_ROLE = lambda role_name: "Successfully added {} Role!".format(
    role_name)

SUCCESS_DEL_ROLE = lambda role_names: "Successfully deleted Role: {}".format(
    role_names)
ERROR_DEL_ROLE = "An error occurred while deleting Role!"

DUPLICATE_ERROR = lambda field_name, table_name: "{} has already been "\
    "used in {}.".format(
        field_name,
        table_name)
ROLE_UPDATE_SUCCESS = lambda username: "Successfully updated {}'s Role!".format(
    username)
