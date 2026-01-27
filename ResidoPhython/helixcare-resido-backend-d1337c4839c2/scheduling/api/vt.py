from rest_framework.permissions import IsAuthenticated

from common.mixins import (
    StandardListBulkCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    StandardListCreateAPIMixin,
)
from scheduling.filters.assignment import VisitTypeAssignmentRequestFilter
from scheduling.filters.vc import VisitCategoryFilter
from scheduling.filters.vt import VisitTypeFilter
from scheduling.filters.vtt import VisitTypeTemplateFilter
from scheduling.models_v2 import (
    VisitCategory,
    VisitType,
    VisitTypeTemplate,
    VisitTypeAssignmentRequest,
)
from scheduling.serializers_v2 import (
    VisitCategorySerializer,
    VisitTypeSerializer,
    VisitTypeTemplateSerializer,
    VisitTypeAssignmentRequestSerializer,
)


class VisitCategoriesListCreateBulkAPIView(StandardListBulkCreateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST put right permission
    queryset = VisitCategory.objects.for_current_user()
    serializer_class = VisitCategorySerializer
    search_fields = ("name", "speciality__specialization", "display_id")
    filter_class = VisitCategoryFilter
    entity = "VisitCategory"


class VisitCategoriesRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST
    queryset = VisitCategory.objects.for_current_user()
    serializer_class = VisitCategorySerializer
    entity = "VisitCategory"


class VisitTypesListCreateBulkAPIView(StandardListBulkCreateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST put right permission
    queryset = VisitType.objects.for_current_user()
    serializer_class = VisitTypeSerializer
    search_fields = ("name", "category__speciality__specialization", "display_id")
    filter_class = VisitTypeFilter
    entity = "VisitType"


class VisitTypesRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST
    queryset = VisitType.objects.for_current_user()
    serializer_class = VisitTypeSerializer
    search_fields = ("name", "display_id")
    entity = "VisitType"


class VisitTypeTemplatesListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST
    queryset = VisitTypeTemplate.objects.for_current_user()
    serializer_class = VisitTypeTemplateSerializer
    search_fields = ("name", "speciality__specialization", "display_id")
    filter_class = VisitTypeTemplateFilter
    entity = "VisitTypeTemplate"


class VisitTypeTemplatesRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST
    queryset = VisitTypeTemplate.objects.for_current_user()
    serializer_class = VisitTypeTemplateSerializer
    filter_class = VisitTypeTemplateFilter
    entity = "VisitTypeTemplate"


class VisitTypeAssignmentRequestListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [IsAuthenticated]  # TODO MUST
    queryset = VisitTypeAssignmentRequest.objects.for_current_user()
    serializer_class = VisitTypeAssignmentRequestSerializer
    search_fields = ("template__display_id", "display_id")
    filter_class = VisitTypeAssignmentRequestFilter
    entity = "VisitTypeAssignmentRequest"
