from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.helix_pagination import StandardPageNumberPagination
from common.mixins import StandardRetrieveAPIMixin, StandardListAPIMixin
from common.response import StandardAPIResponse
from processflow.managers.process.core import ProcessManager
from processflow.models import Process
from processflow.serializers import ProcessTrimmedSerializer


class ProcessListAPIView(StandardListAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardPageNumberPagination
    filterset_fields = (
        "id",
        "object_id",
        "request_id",
        "process_type",
        "status",
        "active",
    )
    queryset = Process.objects.all().order_by("-created_on")
    serializer_class = ProcessTrimmedSerializer


class ProcessRetrieveAPIView(StandardRetrieveAPIMixin):
    permission_classes = (IsAuthenticated,)
    queryset = Process.objects.all()
    serializer_class = ProcessTrimmedSerializer


class TerminateLongRunningProcessesAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        processes_marked_as_failed = (
            ProcessManager.mark_long_running_processes_as_failed()
        )

        response_data = {"total_processes_marked_as_failed": processes_marked_as_failed}
        return StandardAPIResponse(response_data)
