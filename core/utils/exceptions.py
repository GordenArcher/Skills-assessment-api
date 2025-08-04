from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from core.utils.responses import error_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        detail = response.data

        message = "An error occurred."
        errors = detail

        if isinstance(exc, ValidationError):
            message = "Validation failed."
        elif status_code == 403:
            message = "Permission denied."
        elif status_code == 404:
            message = "Resource not found."

        return error_response(
            message=message,
            errors=errors,
            status_code=status_code
        )

    return response
