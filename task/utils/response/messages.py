class ResponseMessages:
    SUCCESS = "Operation completed successfully"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    NOT_FOUND = "Requested resource not found"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Permission denied"
    VALIDATION_ERROR = "Validation error"
    BAD_REQUEST = "Bad request"
    INVALID_REQUEST = "Invalid Request"
    SERVER_ERROR = "Internal server error"
    USER_REGISTERED = "User registered successfully"
    USER_LOGGED_IN = "User logged in successfully"
    USER_LOGGED_OUT = "User logged out successfully"
    INVALID_CREDENTIALS = "Invalid username or password"

def get_message(key_or_message: str, default: str = ResponseMessages.SUCCESS) -> str:
    if hasattr(ResponseMessages, key_or_message):
        return getattr(ResponseMessages, key_or_message)
    return key_or_message or default
