"""
Custom exception handler for DRF
Provides consistent error response format across the API
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status

from app.utils.logger import get_logger

logger = get_logger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF's default handler
    Provides standardized error responses
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception(f"Unhandled exception: {exc}", exc_info=exc)
        return Response(
            {
                "success": False,
                "message": "Internal server error",
                "errors": [],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Extract the error details from DRF's response
    error_data = response.data if isinstance(response.data, dict) else {"detail": response.data}

    # Log the error
    logger.error(
        f"API Error: {context['view'].__class__.__name__} - "
        f"Status: {response.status_code} - Error: {error_data}"
    )

    # Format the response
    formatted_response = {
        "success": False,
        "message": error_data.get("detail", "An error occurred"),
        "errors": error_data,
    }

    return Response(formatted_response, status=response.status_code)
