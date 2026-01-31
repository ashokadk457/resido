from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from app.services.keys_service import KeyService
from app.serializers.key_serializer import KeySerializer
from app.utils.logger import get_logger

logger = get_logger(__name__)


# GET KEYS
@extend_schema(
    tags=["EKeys"],
    description="Get all keys (paginated, sorted)",
    parameters=[
        OpenApiParameter("page", OpenApiTypes.INT, required=False),
        OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        OpenApiParameter("order_by", OpenApiTypes.STR, required=False),
        OpenApiParameter(
            "direction",
            OpenApiTypes.STR,
            required=False,
            enum=["asc", "desc"],
        ),
    ],
    responses=KeySerializer(many=True),
)
@api_view(["GET"])
def get_keys(request):
    logger.info("GET /api/keys")

    keys, meta = KeyService.get_keys(
        page=request.query_params.get("page"),
        page_size=request.query_params.get("page_size"),
        order_by=request.query_params.get("order_by"),
        direction=request.query_params.get("direction"),
    )

    return Response({
        **meta,
        "data": KeySerializer(keys, many=True).data,
    })


# CREATE KEY
@extend_schema(
    tags=["EKeys"],
    request=KeySerializer,
    responses=KeySerializer,
    description="Create a new key",
)
@api_view(["POST"])
def create_key(request):
    logger.info("POST /api/keys")

    serializer = KeySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    key = KeyService.create_key(serializer.validated_data)

    return Response(
        KeySerializer(key).data,
        status=status.HTTP_201_CREATED,
    )


# DELETE KEY
@extend_schema(
    tags=["EKeys"],
    description="Delete key by UUID",
    responses={
        204: None,
        404: {"detail": "Key not found"},
    },
)
@api_view(["DELETE"])
def delete_key(request, key_id):
    logger.info("DELETE /api/keys/%s", key_id)

    deleted = KeyService.delete_key(key_id)

    if not deleted:
        return Response(
            {"detail": "Key not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(status=status.HTTP_204_NO_CONTENT)


# LIST EKEYS
@extend_schema(
    tags=["EKeys"],
    description="List EKeys with filters and pagination",
    parameters=[
        OpenApiParameter("SmartLockId", OpenApiTypes.STR, required=False),
        OpenApiParameter("KeyName", OpenApiTypes.STR, required=False),
        OpenApiParameter("EKeyId", OpenApiTypes.STR, required=False),
        OpenApiParameter("PageNo", OpenApiTypes.INT, required=False),
        OpenApiParameter("PageSize", OpenApiTypes.INT, required=False),
        OpenApiParameter("OrderBy", OpenApiTypes.STR, required=False),
        OpenApiParameter(
            "Direction",
            OpenApiTypes.STR,
            required=False,
            enum=["asc", "desc"],
        ),
    ],
    responses=KeySerializer(many=True),
)
@api_view(["GET"])
def list_ekeys(request):
    logger.info("GET /api/Ekeys/ListEKeys")

    keys, meta = KeyService.list_ekeys(
        smart_lock_id=request.query_params.get("SmartLockId"),
        key_name=request.query_params.get("KeyName"),
        ekey_id=request.query_params.get("EKeyId"),
        page=request.query_params.get("PageNo"),
        page_size=request.query_params.get("PageSize"),
        order_by=request.query_params.get("OrderBy"),
        direction=request.query_params.get("Direction"),
    )

    return Response({
        **meta,
        "data": KeySerializer(keys, many=True).data,
    })
