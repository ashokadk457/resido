from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from common.mixins import StandardListAPIMixin, StandardRetieveAPIMixin
from common.permissions import IsAuthenticatedHelixUser
from .models import AuditEvent
from .serializers import (
    AuditEventListSerializer,
    AuditEventDetailSerializer,
)


class AuditEventListView(StandardListAPIMixin):
    permission_classes = [IsAuthenticatedHelixUser]
    allowed_methods_to_resident = {"get": True}
    serializer_class = AuditEventListSerializer
    entity = "AuditEvent"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    ordering = ("-created_on",)
    search_fields = ("table",)
    filter_fields = ("action",)

    def get_queryset(self):
        user_type = self.request.query_params.get("user_type", None).lower()
        if user_type == "provider":
            queryset = AuditEvent.objects.filter(
                created_by__helixuser_staff__isnull=False, created_by__is_active=True
            ).select_related("created_by__helixuser_staff")
        elif user_type == "patient":
            queryset = AuditEvent.objects.filter(
                created_by__resident__isnull=False, created_by__is_active=True
            ).select_related("created_by__resident")
        else:
            queryset = AuditEvent.objects.all()
        return queryset


class CategoryGetUpdateView(StandardRetieveAPIMixin):
    permission_classes = []
    permission_classes = [IsAuthenticatedHelixUser]
    serializer_class = AuditEventDetailSerializer
    queryset = AuditEvent.objects.all()
    entity = "AuditEvent"
    allowed_methods_to_resident = {"get": True}
