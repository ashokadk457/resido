from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from app.services.keys_service import KeyService
from app.serializers.key_serializer import KeySerializer
from app.models.get_keys_request import GetKeysRequest
from app.models.list_ekeys_request import ListEKeysRequest
from app.models.paging_response import PagingResponse
from app.utils.logger import get_logger
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

logger = get_logger(__name__)

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

    req = GetKeysRequest(
        page=request.query_params.get("page"),
        page_size=request.query_params.get("page_size"),
        order_by=request.query_params.get("order_by"),
        direction=request.query_params.get("direction"),
    )

    keys, meta = KeyService.get_keys(req)

    return Response(
        PagingResponse(
            **meta,
            data=KeySerializer(keys, many=True).data,
        ).to_dict()
    )


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

    req = ListEKeysRequest(
        smart_lock_id=request.query_params.get("SmartLockId"),
        key_name=request.query_params.get("KeyName"),
        ekey_id=request.query_params.get("EKeyId"),
        page=request.query_params.get("PageNo"),
        page_size=request.query_params.get("PageSize"),
        order_by=request.query_params.get("OrderBy"),
        direction=request.query_params.get("Direction"),
    )

    keys, meta = KeyService.list_ekeys(req)

    return Response(
        PagingResponse(
            **meta,
            data=KeySerializer(keys, many=True).data,
        ).to_dict()
    )


@extend_schema(
    tags=["EKeys"],
    request=KeySerializer,
    responses=KeySerializer,
    description="Create a new key",
)
@api_view(["POST"])
def create_key(request):
    serializer = KeySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    key = KeyService.create_key(serializer.validated_data)
    return Response(KeySerializer(key).data, status=status.HTTP_201_CREATED)


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
    deleted = KeyService.delete_key(key_id)

    if not deleted:
        return Response({"detail": "Key not found"}, status=404)

    return Response(status=status.HTTP_204_NO_CONTENT)
