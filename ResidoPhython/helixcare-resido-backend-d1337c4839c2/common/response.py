from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import is_success


class StandardAPIResponse(Response):
    """
    Standard API Response Class as per HelixBeat Standard API Guidelines
    """

    def __init__(
        self,
        data=None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
    ):
        standard_response_data = {
            "status": False if status is None else is_success(status),
        }
        if standard_response_data["status"]:
            standard_response_data["data"] = data
        else:
            standard_response_data["errors"] = data
        super().__init__(
            standard_response_data,
            status,
            template_name,
            headers,
            exception,
            content_type,
        )

    @classmethod
    def from_response(cls, response_obj):
        if isinstance(response_obj, StandardAPIResponse):
            return response_obj
        return StandardAPIResponse(
            data=response_obj.data,
            status=response_obj.status_code,
            headers=response_obj.headers,
        )


def get_diff(current, stored):
    data = []
    fields = current._meta.fields
    for field in fields:
        attr = {}
        new_value = getattr(current, field.name, "")
        old_value = getattr(stored, field.name, "")
        if old_value != new_value:
            attr["field"] = field.name
            attr["existing_value"] = old_value
            attr["new_value"] = new_value
            data.append(attr)
    return data


def handle_conflict(request, target=None):
    try:
        model_name = target.__class__.__name__
        saved = target.__class__._default_manager.get(pk=target.pk)
        diff = get_diff(target, saved)
    except target.__class__.DoesNotExist:
        saved = None
        diff = None
        model_name = None
    return JsonResponse(
        {"data": {"model": model_name, "values": diff}}, status=status.HTTP_409_CONFLICT
    )
