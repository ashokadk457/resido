from rest_framework import generics

from assets.models import Asset
from assets.serializers import AssetSerializer
from common.permissions import (
    IsAuthenticatedHelixUser,
    IsAuthenticatedResidentPermission,
)


class AssetListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedHelixUser | IsAuthenticatedResidentPermission,)
    allowed_methods_to_resident = {"get": True, "post": True}
    serializer_class = AssetSerializer

    def get_queryset(self):
        return Asset.objects.filter(created_by=self.request.user)


class AssetDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticatedHelixUser | IsAuthenticatedResidentPermission,)
    allowed_methods_to_resident = {"get": True}
    serializer_class = AssetSerializer

    def get_queryset(self):
        return Asset.objects.filter(created_by=self.request.user)
