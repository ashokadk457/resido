import pandas as pd

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.views import APIView
from django.db import transaction

from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
)
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException, StandardAPIResponse
from data.models import ReasonCategory, Reason
from data.serializers import (
    ReasonCategorySerializer,
    ReasonSerializer,
    ReasonBulkUploadSerializer,
)
from data.filters import ReasonFilter


class ReasonCategoryListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ReasonCategorySerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ReasonCategory"
    queryset = ReasonCategory.objects.for_current_user()
    search_fields = ("policy_name",)
    filterset_fields = ("status",)


class ReasonCategoryDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentDocument"
    queryset = ReasonCategory.objects.for_current_user()
    serializer_class = ReasonCategorySerializer


class ReasonListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ReasonSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Reason"
    queryset = Reason.objects.for_current_user()
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    filterset_class = ReasonFilter


class ReasonDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Reason"
    queryset = Reason.objects.for_current_user()
    serializer_class = ReasonSerializer


class ReasonBulkUploadAPIView(StandardListCreateAPIMixin):
    serializer_class = ReasonBulkUploadSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Reason.objects.for_current_user()
    entity = "Reason"

    def post(self, request, *args, **kwargs):
        excel_file = request.FILES.get("file")
        if not excel_file:
            raise StandardAPIException(
                code="no_file_provided",
                detail=ERROR_DETAILS["no_file_provided"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            raise StandardAPIException(
                code="no_file_provided",
                detail=f"{ERROR_DETAILS['no_file_provided']}: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        required_columns = {"category", "name", "description", "status"}
        missing = required_columns - set(df.columns)
        if missing:
            raise StandardAPIException(
                code="columns_missed",
                detail={"error": f"Missing columns: {', '.join(missing)}"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        records = []
        for _, row in df.iterrows():
            records.append(
                Reason(
                    category_id=row["category"],  # must be ID
                    name=row["name"],
                    description=row.get("description", ""),
                    status=row.get("status", True),
                )
            )

        with transaction.atomic():
            Reason.objects.bulk_create(records, ignore_conflicts=True)

        return StandardAPIResponse(
            {"status": "Bulk upload successful", "records_uploaded": len(records)},
            status=status.HTTP_201_CREATED,
        )


class ReasonModuleCountAPIView(APIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]

    def get(self, request, *args, **kwargs):
        reason_module_counts = {
            "reason_categories": ReasonCategory.objects.count(),
            "reasons": Reason.objects.count(),
        }
        return StandardAPIResponse(data=reason_module_counts, status=status.HTTP_200_OK)
