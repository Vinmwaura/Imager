"""
Constants
"""
# Min and Max length of First and Last names
MIN_NAMES = 2
MAX_NAMES = 20

# Error Messages
CLIENT_CREATION_ERROR = "An Error occured creating client, "\
    "please try again in a while."

INVALID_FIELD_LENGTH = lambda field_min, field_max: 'Field must be between {} and {} characters.'.format(
    field_min, field_max)
