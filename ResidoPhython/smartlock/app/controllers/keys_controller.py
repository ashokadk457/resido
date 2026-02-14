"""
Keys Controller Module - Handles electronic key operations
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from app.services.keys_service import KeyService
from app.serializers.key_serializer import KeySerializer
from app.models.get_keys_request import GetKeysRequest
from app.models.list_ekeys_request import ListEKeysRequest
from app.models.paging_response import PagingResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EKeyListController(APIView):
    """
    Controller for listing electronic keys.
    Handles retrieval of all keys with pagination and sorting.
    """

    @extend_schema(
        tags=["EKeys"],
        summary="Get all electronic keys",
        description="Retrieve paginated list of electronic keys with optional sorting",
        parameters=[
            OpenApiParameter(
                "page",
                OpenApiTypes.INT,
                required=False,
                description="Page number (default: 1)"
            ),
            OpenApiParameter(
                "page_size",
                OpenApiTypes.INT,
                required=False,
                description="Items per page (default: 50)"
            ),
            OpenApiParameter(
                "order_by",
                OpenApiTypes.STR,
                required=False,
                description="Sort field (default: created_at)"
            ),
            OpenApiParameter(
                "direction",
                OpenApiTypes.STR,
                required=False,
                enum=["asc", "desc"],
                description="Sort direction"
            ),
        ],
        responses={
            200: {"type": "object"},
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request):
        """
        Get all keys with pagination and sorting.
        
        Args:
            request: HTTP request with optional query parameters
            
        Returns:
            Paginated list of electronic keys
        """
        logger.info("GET /api/v1/ekeys")

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


class EKeyCreateController(APIView):
    """
    Controller for creating electronic keys.
    Handles creation of new electronic keys.
    """

    @extend_schema(
        tags=["EKeys"],
        summary="Create new electronic key",
        description="Create a new electronic key",
        request=KeySerializer,
        responses={
            201: KeySerializer,
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def post(self, request):
        """
        Create a new electronic key.
        
        Args:
            request: HTTP request with key data
            
        Returns:
            Created key object
        """
        logger.info("POST /api/v1/ekeys/create")

        serializer = KeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        key = KeyService.create_key(serializer.validated_data)
        return Response(KeySerializer(key).data, status=status.HTTP_201_CREATED)


class EKeyDetailController(APIView):
    """
    Controller for individual electronic key operations.
    Handles retrieval, update, and deletion of specific keys.
    """

    @extend_schema(
        tags=["EKeys"],
        summary="Delete electronic key",
        description="Delete an electronic key by ID",
        responses={
            204: None,
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def delete(self, request, key_id):
        """
        Delete an electronic key.
        
        Args:
            request: HTTP request
            key_id: UUID of the key to delete
            
        Returns:
            204 No Content if successful, 404 if not found
        """
        logger.info(f"DELETE /api/v1/ekeys/{key_id}")

        deleted = KeyService.delete_key(key_id)

        if not deleted:
            return Response(
                {"detail": "Key not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class EKeySearchController(APIView):
    """
    Controller for searching and filtering electronic keys.
    Handles advanced filtering with multiple parameters.
    """

    @extend_schema(
        tags=["EKeys"],
        summary="List EKeys with filters",
        description="List electronic keys with advanced filtering and pagination",
        parameters=[
            OpenApiParameter(
                "SmartLockId",
                OpenApiTypes.STR,
                required=False,
                description="Filter by Smart Lock ID"
            ),
            OpenApiParameter(
                "KeyName",
                OpenApiTypes.STR,
                required=False,
                description="Filter by key name"
            ),
            OpenApiParameter(
                "EKeyId",
                OpenApiTypes.STR,
                required=False,
                description="Filter by EKey ID"
            ),
            OpenApiParameter(
                "PageNo",
                OpenApiTypes.INT,
                required=False,
                description="Page number (default: 1)"
            ),
            OpenApiParameter(
                "PageSize",
                OpenApiTypes.INT,
                required=False,
                description="Items per page (default: 50)"
            ),
            OpenApiParameter(
                "OrderBy",
                OpenApiTypes.STR,
                required=False,
                description="Sort field"
            ),
            OpenApiParameter(
                "Direction",
                OpenApiTypes.STR,
                required=False,
                enum=["asc", "desc"],
                description="Sort direction"
            ),
        ],
        responses={
            200: {"type": "object"},
            401: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    def get(self, request):
        """
        Search electronic keys with filters.
        
        Args:
            request: HTTP request with optional filter parameters
            
        Returns:
            Filtered and paginated list of electronic keys
        """
        logger.info("GET /api/v1/ekeys/search")

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
