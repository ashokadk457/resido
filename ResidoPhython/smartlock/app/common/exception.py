import json

from keycloak import KeycloakError, KeycloakAuthenticationError
from rest_framework.exceptions import APIException, ErrorDetail

from common.errors import ERROR_DETAILS
from common.response import StandardAPIResponse
from common.utils.logging import logger
from rest_framework.utils.serializer_helpers import ReturnDict


class StandardAPIException(APIException):
    """
    Exception class to throw standard API Exceptions with error_code and user-friendly
    error_message.
    """

    status_code = 400
    default_code = "error"
    default_detail = "Error Occurred"
    default_info = None

    def __init__(self, code, detail, status_code, info=None):
        super().__init__(detail=detail, code=code)
        self.code = code if code else self.default_code
        self.info = info
        self.status_code = status_code


class StandardExceptionHandler:
    """
    Exception Handler class to handle and report API exceptions as per
    HelixBeat API Style Guide.
    """

    @classmethod
    def super_handle(cls, exc, context):
        from rest_framework.views import exception_handler

        response = exception_handler(exc, context)
        whitelisted = cls.is_path_whitelisted(context=context)
        return cls.handle(exc=exc, response=response, whitelisted=whitelisted)

    @classmethod
    def handle(cls, exc, response, whitelisted=True):
        if not whitelisted:
            return response

        try:
            if response is not None and isinstance(exc, StandardAPIException):
                return cls._handle_standard_api_exception(exc, response)

            if response is not None and isinstance(exc, APIException):
                return cls._handle_inbuilt_api_exception(exc, response)

            if isinstance(exc, KeycloakError):
                return cls._handle_keycloak_exception(exc)

            if isinstance(exc, KeycloakAuthenticationError):
                return cls._handle_keycloak_exception(exc)

        except Exception as e:
            logger.error(f"Exception occurred while parsing API exception: {str(e)}")

        return response

    @classmethod
    def rectify_error_message(cls, errors_data):
        if not errors_data:
            return errors_data

        for error in errors_data:
            error_message = error.get("message")
            if error_message == "token_not_valid":
                error_message = ERROR_DETAILS.get("token_not_valid")
            error["message"] = error_message

        return errors_data

    @classmethod
    def is_path_whitelisted(cls, context):
        # path = context.get("request")._request.path
        return True

    @classmethod
    def _handle_keycloak_exception(cls, exc):
        status_code = exc.response_code
        error_dict = json.loads(exc.error_message.decode("utf-8"))
        code = error_dict.get("error")
        if not code:
            code = error_dict.get("errorMessage")
        message = error_dict.get("error_description")
        if not message:
            message = error_dict.get("errorMessage")
        field = None
        if error_dict.get("field"):
            field = error_dict.get("field")

        standard_error_dict = {"code": code, "message": message}
        if field:
            standard_error_dict["field"] = field
        errors_data = [standard_error_dict]
        errors_data = cls.rectify_error_message(errors_data=errors_data)
        return StandardAPIResponse(
            data=errors_data,
            status=status_code,
        )

    @classmethod
    def _handle_standard_api_exception(cls, exc, response):
        error_code, error_message = None, None
        if hasattr(exc, "code"):
            error_code = getattr(exc, "code")
        if hasattr(exc, "detail"):
            error_message = exc.detail.__str__()
        errors_data = [{"code": error_code, "message": error_message}]
        errors_data = cls.rectify_error_message(errors_data=errors_data)
        return StandardAPIResponse(
            data=errors_data,
            status=response.status_code,
            headers=response.headers,
        )

    @classmethod
    def flatten_error_detail(cls, error_detail, parent_key=""):
        items = []
        for key, value in error_detail.items():
            new_key = parent_key + "." + key if parent_key else key
            if isinstance(value, dict):
                items.extend(cls.flatten_error_detail(value, new_key).items())
            else:
                items.append((new_key, value))
        return dict(items)

    @classmethod
    def _handle_inbuilt_api_exception(cls, exc, response):
        errors_data = []
        if hasattr(exc, "detail"):
            error_detail = exc.detail
            errors_data = []
            if isinstance(error_detail, list):
                for error in error_detail:
                    errors_data.append({"code": error.code, "message": error.__str__()})
            elif isinstance(error_detail, ErrorDetail):
                errors_data.append(
                    {"code": error_detail.code, "message": error_detail.__str__()}
                )
            elif isinstance(error_detail, dict):
                error_detail = cls.flatten_error_detail(error_detail)
                code = error_detail.get("code")
                if isinstance(code, ErrorDetail):
                    errors_data.append({"code": code.code, "message": code.__str__()})
                if code is None:
                    for k, v in error_detail.items():
                        if isinstance(v, list):
                            v_0 = v[0]
                            error_data = {
                                "code": v_0.code,
                                "message": v_0.__str__(),
                                "field": k,
                            }
                            errors_data.append(error_data)
            elif isinstance(error_detail, ReturnDict):
                detail = list(error_detail.values())[0]
                if isinstance(detail, list):
                    for error in detail:
                        errors_data.append(
                            {"code": error.code, "message": error.__str__()}
                        )
                if isinstance(detail, ErrorDetail):
                    errors_data.append(
                        {"code": detail.code, "message": detail.__str__()}
                    )
        errors_data = cls.rectify_error_message(errors_data=errors_data)
        return StandardAPIResponse(
            data=errors_data,
            status=response.status_code,
            headers=response.headers,
        )


def standard_api_exception_handler(exc, context):
    """
    Exception Handler function that invokes the HelixBeat standard API exception handler

    Args:
        exc:
        context:

    Returns:

    """
    return StandardExceptionHandler.super_handle(exc, context)
