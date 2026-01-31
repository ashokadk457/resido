from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from app.serializers.ttlock_token_request_serializer import TTLockTokenRequestSerializer
from app.serializers.ttlock_token_response_serializer import TTLockTokenResponseSerializer
from app.services.ttlock_token_service import fetch_ttlock_token
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from app.utils.logger import get_logger
import hashlib


logger = get_logger(__name__)

@extend_schema(
    tags=["Fetch TTLock Token"],
    parameters=[
        OpenApiParameter("username", OpenApiTypes.STR, required=True),
        OpenApiParameter("password", OpenApiTypes.STR, required=True)
    ]
)
@api_view(['POST'])
def ttlock_token_view(request):
    request.data['clientId'] = '5eb489f4b1f645d8ab7c95f7fe3e043c'
    request.data['clientSecret'] = '91e0f8fbec6a8be1ba14cb6c793635a2'
    request.data['username'] = "Ashokpatel457@gmail.com"
    # Encrypt password to MD5
    plain_password = ""
    md5_password = hashlib.md5(plain_password.encode('utf-8')).hexdigest()
    request.data['password'] ="ae1be7237828a4db0dd762a9455f5495";
    logger.info(request.data);
    serializer = TTLockTokenRequestSerializer(data=request.data)
    if serializer.is_valid():
        result = fetch_ttlock_token(serializer.validated_data)
        response_serializer = TTLockTokenResponseSerializer(data=result)
        if response_serializer.is_valid():
            logger.info( Response(response_serializer.data, status=status.HTTP_200_OK));
            logger.info("TTLock Token Result: %s", result);
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)