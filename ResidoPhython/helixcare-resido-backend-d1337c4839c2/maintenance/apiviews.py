from rest_framework import status
from rest_framework.response import Response
from django.db.models import Count
from datetime import datetime
from django.utils import timezone
from rest_framework import generics

from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    CountAPIMixin,
)
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.response import StandardAPIResponse
from maintenance.models import (
    ServiceProviderDocument,
    ServiceProvider,
    ServiceProviderReview,
    Maintenance,
)
from maintenance.serializers import (
    ServiceProviderSerializer,
    ServiceProviderDetailSerializer,
    ServiceProviderDocumentSerializer,
    ServiceProviderReviewSerializer,
    ServiceProviderReviewListSerializer,
    MaintenanceSerializer,
    MaintenanceStatusUpdateSerializer,
    MaintenanceAssignSerializer,
)
from maintenance.constants import MaintenanceStatus
from maintenance.filters import (
    ServiceProviderFilter,
    ServiceProviderReviewFilter,
    MaintenanceFilter,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter


class ServiceProviderListCreateView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "ServiceProvider"
    serializer_class = ServiceProviderSerializer
    queryset = ServiceProvider.objects.all()
    filterset_class = ServiceProviderFilter
    search_fields = [
        "service_type",
        "name",
        "contact_name",
        "languages_known",
    ]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ServiceProviderDetailSerializer
        return ServiceProviderSerializer


class ServiceProviderDetailUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    entity = "ServiceProvider"
    queryset = ServiceProvider.objects.for_current_user()
    serializer_class = ServiceProviderSerializer

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ServiceProviderDetailSerializer
        return ServiceProviderSerializer


class ServiceProviderDocumentListCreateView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "ServiceProviderDocument"
    serializer_class = ServiceProviderDocumentSerializer
    queryset = ServiceProviderDocument.objects.all()
    filterset_fields = [
        "service_provider",
        "is_primary",
        "document_type",
        "active",
    ]
    search_fields = [
        "document_type",
        "service_provider__name",
        "service_provider__contact_name",
    ]


class ServiceProviderDocumentDetailUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    entity = "ServiceProviderDocument"
    queryset = ServiceProviderDocument.objects.for_current_user()
    serializer_class = ServiceProviderDocumentSerializer


class ServiceProviderPhoneListView(generics.ListAPIView):
    permission_classes = [HelixUserBasePermission]
    queryset = ServiceProvider.objects.all()
    filterset_class = ServiceProviderFilter
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ["name", "phone"]

    def get(self, request, *args, **kwargs):
        # Apply filters
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.values_list(
            "id", "phone", "name", "contact_name"
        ).distinct()

        results = [
            {
                "id": item[0],
                "phone": item[1],
                "service_provider_name": item[2],
                "contact_person": item[3],
            }
            for item in queryset
        ]

        return StandardAPIResponse(
            data={"values": results},
            status=status.HTTP_200_OK,
        )


class MaintenancetListCreateView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    entity = "Maintenance"
    serializer_class = MaintenanceSerializer
    queryset = Maintenance.objects.all()
    filterset_class = MaintenanceFilter
    search_fields = [
        "display_id",
        "status",
        "service_type",
        "resident__user__first_name",
        "resident__user__last_name",
        "assignee__name",
        "assignee__contact_name",
        "preferred_vendor__name",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        created_on_after = self.request.query_params.get("created_on_after")
        created_on_before = self.request.query_params.get("created_on_before")
        due_date_after = self.request.query_params.get("due_date_after")
        due_date_before = self.request.query_params.get("due_date_before")
        status_filter = self.request.query_params.get("status")

        if created_on_after:
            queryset = queryset.filter(created_on__date__gte=created_on_after)
        if created_on_before:
            queryset = queryset.filter(created_on__date__lte=created_on_before)
        if due_date_after:
            queryset = queryset.filter(due_date__gte=due_date_after)
        if due_date_before:
            queryset = queryset.filter(due_date__lte=due_date_before)

        if status_filter:
            if status_filter == "assigned":
                queryset = queryset.filter(assignee__isnull=False)
            elif status_filter == "closed":
                queryset = queryset.filter(status=MaintenanceStatus.COMPLETED.value)
            elif status_filter == "escalated":
                queryset = queryset.filter(service_priority="EMERG")
            else:
                queryset = queryset.filter(status=status_filter)

        return queryset


class MaintenanceDetailUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Maintenance"
    queryset = Maintenance.objects.for_current_user()
    serializer_class = MaintenanceSerializer


class MaintenanceCountAPIView(CountAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Maintenance"
    queryset = Maintenance.objects.for_current_user()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "open": {"field": "status", "condition": {"status": "open"}},
        "assigned": {"field": "assignee", "condition": {"assignee__isnull": False}},
        "in_progress": {"field": "status", "condition": {"status": "in_progress"}},
        "closed": {"field": "status", "condition": {"status": "completed"}},
        "escalated": {
            "field": "service_priority",
            "condition": {"service_priority": "EMERG"},
        },
    }


class ServiceProviderReviewListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    entity = "ServiceProviderReview"
    serializer_class = ServiceProviderReviewSerializer
    queryset = ServiceProviderReview.objects.all()
    filterset_class = ServiceProviderReviewFilter
    search_fields = [
        "reviewer_name",
        "review_text",
        "service_provider__name",
    ]
    ordering_fields = [
        "created_on",
        "rating",
        "updated_on",
    ]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ServiceProviderReviewListSerializer
        return ServiceProviderReviewSerializer


class ServiceProviderCountAPIView(CountAPIMixin):
    permission_classes = [HelixUserBasePermission]
    entity = "ServiceProvider"
    queryset = ServiceProvider.objects.all()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "active": {"field": "active", "condition": {"active": True}},
        "inactive": {"field": "active", "condition": {"active": False}},
    }

    def get(self, request, *args, **kwargs):
        data = {
            "all": ServiceProvider.objects.count(),
            "active": ServiceProvider.objects.filter(active=True).count(),
            "inactive": ServiceProvider.objects.filter(active=False).count(),
            "by_service_type": {},
            "by_rating": {
                "5_star": ServiceProvider.objects.filter(
                    overall_rating__gte=4.5
                ).count(),
                "4_star": ServiceProvider.objects.filter(
                    overall_rating__gte=3.5, overall_rating__lt=4.5
                ).count(),
                "3_star": ServiceProvider.objects.filter(
                    overall_rating__gte=2.5, overall_rating__lt=3.5
                ).count(),
                "2_star": ServiceProvider.objects.filter(
                    overall_rating__gte=1.5, overall_rating__lt=2.5
                ).count(),
                "1_star": ServiceProvider.objects.filter(
                    overall_rating__lt=1.5
                ).count(),
            },
        }

        service_types = (
            ServiceProvider.objects.values("service_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        for item in service_types:
            data["by_service_type"][item["service_type"]] = item["count"]

        return Response({"status": True, "data": data})


class MaintenanceStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = MaintenanceStatusUpdateSerializer
    queryset = Maintenance.objects.all()
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        maintenance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")

        maintenance.status = new_status

        if new_status == MaintenanceStatus.REJECTED.value:
            maintenance.reject_reason = serializer.validated_data.get("reject_reason")
            maintenance.reject_notes = serializer.validated_data.get("reject_notes")
            maintenance.reject_date = datetime.now().date()

        if new_status == MaintenanceStatus.COMPLETED.value:
            maintenance.resolved_date = datetime.now().date()

        maintenance.updated_by = request.user
        maintenance.updated_on = timezone.now()
        maintenance.save()

        response_serializer = MaintenanceSerializer(
            maintenance, context={"request": request}
        )
        return StandardAPIResponse(
            data=response_serializer.data, status=status.HTTP_200_OK
        )


class MaintenanceAssignView(generics.UpdateAPIView):
    permission_classes = [HelixUserBasePermission]
    serializer_class = MaintenanceAssignSerializer
    queryset = Maintenance.objects.all()
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        maintenance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_assignee = serializer.validated_data.get("assignee")

        maintenance.assignee = new_assignee
        maintenance.status = MaintenanceStatus.APPROVED.value
        maintenance.assigned_on = timezone.now()
        maintenance.assigned_by = request.user
        maintenance.updated_by = request.user
        maintenance.updated_on = timezone.now()
        maintenance.save()

        response_serializer = MaintenanceSerializer(
            maintenance, context={"request": request}
        )
        return StandardAPIResponse(
            data=response_serializer.data, status=status.HTTP_200_OK
        )


class MaintenancePriorityUpdateView(generics.UpdateAPIView):
    permission_classes = [HelixUserBasePermission]
    queryset = Maintenance.objects.all()
    lookup_field = "pk"

    def patch(self, request, *args, **kwargs):
        maintenance = self.get_object()
        new_priority = request.data.get("priority")

        if not new_priority:
            return StandardAPIResponse(
                data={"priority": ["This field may not be blank."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        maintenance.service_priority = new_priority
        maintenance.updated_by = request.user
        maintenance.updated_on = timezone.now()
        maintenance.save()

        response_serializer = MaintenanceSerializer(
            maintenance, context={"request": request}
        )
        return StandardAPIResponse(
            data=response_serializer.data, status=status.HTTP_200_OK
        )
