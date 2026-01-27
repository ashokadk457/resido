import django_filters

from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

# from silk.profiling.profiler import silk_profile

from common.errors import ERROR_DETAILS
from common.utils.general import is_valid_uuid
from common.exception import StandardAPIException
from common.mixins import StandardListCreateAPIMixin, StandardRetrieveUpdateAPIMixin
from common.permissions import HelixUserBasePermission
from common.response import StandardAPIResponse
from helixauth.authentication.kc import KeyCloakAuthentication
from helixauth.utils import create_verification_code
from helixauth.utils import get_users
from staff.models import HelixStaff, StaffGroup
from staff.constants import StaffStatus
from helixauth.constants import CREATE_PASSWORD_URL
from notifications.managers.notification import NotificationsManager
from staff.serializers import (
    StaffSerializer,
    InviteStaffSerializer,
    StaffMinDetailSerializer,
    StaffGroupSerializer,
    StaffGroupDetailSerializer,
)


class StaffFilterSet(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(
        field_name="employee_id", lookup_expr="icontains"
    )
    location = django_filters.CharFilter(field_name="locations", lookup_expr="exact")
    status = django_filters.CharFilter(
        field_name="user__status", lookup_expr="icontains"
    )
    locked = django_filters.BooleanFilter(
        field_name="user__locked", lookup_expr="exact"
    )
    first_name = django_filters.CharFilter(
        field_name="user__first_name", lookup_expr="icontains"
    )
    last_name = django_filters.CharFilter(
        field_name="user__last_name", lookup_expr="icontains"
    )
    middle_name = django_filters.CharFilter(
        field_name="user__middle_name", lookup_expr="icontains"
    )
    preferred_name = django_filters.CharFilter(
        field_name="user__preferred_name", lookup_expr="icontains"
    )
    zipcode = django_filters.CharFilter(
        field_name="user__zipcode", lookup_expr="icontains"
    )
    city = django_filters.CharFilter(field_name="user__city", lookup_expr="icontains")
    state = django_filters.CharFilter(field_name="user__state", lookup_expr="icontains")
    short_name = django_filters.CharFilter(
        field_name="user__short_name", lookup_expr="icontains"
    )
    is_active = django_filters.BooleanFilter(
        field_name="user__is_active", lookup_expr="icontains"
    )
    gender = django_filters.CharFilter(field_name="user__gender", lookup_expr="iexact")

    class Meta:
        model = HelixStaff
        fields = (
            "display_id",
            "is_active",
            "city",
            "zipcode",
            "first_name",
            "last_name",
            "gender",
            "status",
            "state",
            "location",
            "locked",
            "middle_name",
            "preferred_name",
            "short_name",
        )


class StaffInviteMixin:
    def _send_welcome_email(self, staff):
        mngr = NotificationsManager(user=staff, event_type=4)
        subject = f"Welcome {staff.user.first_name}!"
        code = create_verification_code(
            user_id=str(staff.user.id), user_type=1, channel="EMAIL"
        )
        domain = self.request.tenant.domain
        url = CREATE_PASSWORD_URL.format(
            domain=domain, user_id=str(staff.user.id), code=code, user_type=1
        )
        body = f"Please click on link to activate account & set password -> {url}"
        mngr.send_email(subject=subject, body=body)


class StaffListCreate(StandardListCreateAPIMixin, StaffInviteMixin):
    permission_classes = [HelixUserBasePermission]
    authentication_classes = [KeyCloakAuthentication]
    entity = "HelixStaff"
    queryset = (
        HelixStaff.objects.for_current_user()
        .select_related(
            "user",
        )
        .prefetch_related(
            "customers",
            "properties",
            "locations",
            "buildings",
            "floors",
            "units",
        )
        .order_by("-created_on")
    )  # Everyone has access to Provider details
    serializer_class = StaffSerializer
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__middle_name",
        "user__email",
        "user_roles__role_name",
        "display_id",
    )
    filterset_class = StaffFilterSet
    ordering_fields = ("user__first_name", "user__last_name", "user__status", "type")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InviteStaffSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        super().perform_create(serializer)
        staff = serializer.instance
        self._send_welcome_email(staff=staff)


class StaffDetailAPIView(generics.RetrieveUpdateAPIView):
    # Depending on the type of access, we reveal the amount of details
    # of the provider
    serializer_class_retrieve_partial_detail = StaffMinDetailSerializer
    serializer_class_retrieve = StaffSerializer
    entity = "HelixStaff"
    queryset = (
        HelixStaff.objects.for_current_user()
        .select_related(
            "user",
        )
        .prefetch_related(
            "customers",
            "properties",
            "locations",
            "buildings",
            "floors",
            "units",
        )
    )  # Everyone has access to Provider details

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if not self.request.user.is_authenticated:
            return self.serializer_class_retrieve_partial_detail
        return self.serializer_class_retrieve

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.update(serializer.instance, serializer.validated_data)


class ResendInviteAPIView(generics.GenericAPIView, StaffInviteMixin):
    permission_classes = (HelixUserBasePermission,)
    entity = "HelixStaff"

    def post(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")
        user_ids = (
            [user_id] if user_id is not None else request.data.get("user_ids", [])
        )
        if not isinstance(user_ids, list) or not any(
            is_valid_uuid(uid) for uid in user_ids
        ):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        users = get_users(user_ids)
        if not users.exists():
            return Response(
                {"message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        sent_to = []
        for user in users:
            if user.is_staff:
                self._send_welcome_email(user.helixuser_staff)
                sent_to.append(user.username)

        return StandardAPIResponse(
            {
                "message": "Verification email sent again",
                "updated_ids": sent_to,
                "not_updated_ids": [
                    user.id for user in users if str(user.id) not in user_ids
                ],
            },
            status=status.HTTP_200_OK,
        )


class StaffCountView(generics.GenericAPIView):
    permission_classes = (HelixUserBasePermission,)
    entity = "HelixStaff"

    def get(self, request, *args, **kwargs):
        q = HelixStaff.objects.for_current_user().select_related("user")
        q = q.annotate(
            active=Count(
                "user__status", filter=Q(user__status=StaffStatus.APPROVED.value)
            )
        )
        q = q.annotate(
            inactive=Count(
                "user__status", filter=Q(user__status=StaffStatus.REJECTED.value)
            )
        )
        q = q.annotate(
            pending=Count(
                "user__status", filter=Q(user__status=StaffStatus.PENDING.value)
            )
        )
        q = q.annotate(locked=Count("user__locked", filter=Q(user__locked=True)))
        q = q.aggregate(Sum("active"), Sum("inactive"), Sum("pending"), Sum("locked"))
        group_count = StaffGroup.objects.all().count()
        return StandardAPIResponse(
            data={
                "active": q.get("active__sum", 0),
                "inactive": q.get("inactive__sum", 0),
                "pending": q.get("pending__sum", 0),
                "locked": q.get("locked__sum", 0),
                "user_groups": group_count,
            },
            status=status.HTTP_200_OK,
        )


class StaffGroupsListCreate(StandardListCreateAPIMixin):
    permission_classes = (AllowAny,)
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    entity = "StaffGroup"

    def get_queryset(self):
        if self.request.query_params.get("is_count", "") == "false":
            self.pagination_class = None
        return (
            StaffGroup.objects.all()
            .prefetch_related("staff")
            .annotate(count=Count("staff"))
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StaffGroupDetailSerializer
        return StaffGroupSerializer


class StaffGroupsGetUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (AllowAny,)
    serializer_class = StaffGroupDetailSerializer
    queryset = StaffGroup.objects.all().prefetch_related(
        "staff", "staff__user", "staff__user__profile_img"
    )
    entity = "StaffGroup"
