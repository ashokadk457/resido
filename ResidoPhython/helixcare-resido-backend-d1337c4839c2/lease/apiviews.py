from rest_framework import status
from rest_framework.generics import GenericAPIView
from lease.models import (
    Application,
    Lease,
    LeaseOtherOccupants,
    LeaseLateFees,
    LeaseAdditionalSigners,
    LeasePetsAllowed,
    LeaseUtilityServices,
    LeaseKeys,
    LeasePromotionalDiscount,
    LeaseOneTimeFees,
    MoveRequest,
    MoveInspectionLog,
)
from lease.serializers import (
    ApplicationSerializerForStaff,
    LeaseSerialiserForStaff,
    LeaseOtherOccupantsSerializer,
    LeaseLateFeesSerializer,
    LeaseAdditionalSignersSerializer,
    LeasePetsAllowedSerializer,
    LeaseUtilityServicesSerializer,
    LeaseKeysSerializer,
    LeaseOneTimeFeesSerializer,
    LeasePromotionalDiscountSerializer,
    ApplicationSerializerForResident,
    LeaseSerializerForResident,
    LeaseSerializerV2,
    MoveRequestSerializer,
    MoveRequestMinimalSerializer,
    PropertyDetailSerializer,
    MoveRequestInspectionLogSerializer,
    ApplicationVIewSerializer,
    ApplicationMinimalSerializer,
)
from lease.constants import LeaseApplicationStatus
from lease.filters import LeaseFilters, MoveRequestFilter
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
    IsAuthenticatedHelixUser,
)
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    CountAPIMixin,
    StandardListAPIMixin,
)
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.response import StandardAPIResponse

from helixauth.authentication.composite.guest import ResidentCompositeAuthentication

from common.utils.general import is_valid_uuid, is_resident_request
from common.utils.logging import logger
from lease.managers.application import ApplicationManager
from django_filters import rest_framework as filters
from django_filters.filters import UUIDFilter


class ApplicationFilter(filters.FilterSet):
    property = UUIDFilter(field_name="unit__floor__building__location__property")
    location = UUIDFilter(field_name="unit__floor__building__location")
    building = UUIDFilter(field_name="unit__floor__building")
    floor = UUIDFilter(field_name="unit__floor")

    class Meta:
        model = Application
        fields = {
            "resident": ["exact"],
            "unit": ["exact"],
            "status": ["exact"],
            "sent_date": ["exact", "gte", "lte"],
            "received_date": ["exact", "gte", "lte"],
            "reject_date": ["exact", "gte", "lte"],
        }


class ApplicationListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__display_id",
        "unit__unit_type",
        "unit__floor_plan",
        "unit__unit_number",
    )
    filterset_class = ApplicationFilter

    queryset = Application.objects.for_current_user().select_related(
        "unit",
        "unit__floor",
        "unit__floor__building",
        "unit__floor__building__location",
        "unit__floor__building__location__property",
    )
    serializer_class = ApplicationSerializerForStaff
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "Application"


class ApplicationGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    # authentication_classes = [
    #     KeyCloakAuthentication,
    #     ResidentRentalRequestAuthentication,
    #     RentalApplicationAuthentication,
    # ]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "patch": True}
    queryset = Application.objects.for_current_user().select_related(
        "unit",
        "unit__floor",
        "unit__floor__building",
        "unit__floor__building__location",
        "unit__floor__building__location__property",
    )
    entity = "Application"

    def get_serializer_class(self):
        if is_resident_request(self.request):
            return ApplicationSerializerForResident
        return ApplicationSerializerForStaff


class ApplicationMinimalListView(StandardListAPIMixin):
    """
    Minimal lease application list API
    """

    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__display_id",
        "unit__unit_number",
    )
    filterset_class = ApplicationFilter
    serializer_class = ApplicationMinimalSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    entity = "Application"

    def get_queryset(self):
        return Application.objects.for_current_user().select_related(
            "resident__user",
            "resident__user__profile_img",
            "unit__floor__building__location__property",
        )


class ApplicationResendInviteView(GenericAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "Application"

    def post(self, request, *args, **kwargs):
        ids = request.data.get("application_ids", [])
        if not ids:
            raise StandardAPIException(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param="application_ids"
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        is_valid_ids = all([True if is_valid_uuid(i) else False for i in ids])
        if not is_valid_ids:
            raise StandardAPIException(
                code="invalid_value",
                detail=ERROR_DETAILS["invalid_value"].format(attr="application_ids"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        objs = Application.objects.for_current_user().filter(
            id__in=ids, status=LeaseApplicationStatus.SENT.value
        )
        if not objs.exists():
            raise StandardAPIException(
                code="application_not_found",
                detail=ERROR_DETAILS["application_not_found"].format(
                    obj_type="Application"
                ),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        sent_to = []
        for obj in objs:
            try:
                mngr = ApplicationManager(obj)
                mngr.send_email()
                sent_to.append(obj.id)
            except Exception as e:
                logger.error(
                    f"Error resending email for application: {obj.id}, error: {e}"
                )
        resp = {"sent_to": sent_to}
        return StandardAPIResponse(data=resp, status=status.HTTP_200_OK)


class ApplicationCountView(CountAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = Application.objects.for_current_user()
    count_label_to_field_condition_map = {
        "received": {"field": "status", "condition": {"status": "received"}},
        "sent": {"field": "status", "condition": {"status": "sent"}},
        "rejected": {"field": "status", "condition": {"status": "rejected"}},
        "approved": {"field": "status", "condition": {"status": "approved"}},
    }
    entity = "Application"


class LeaseListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__display_id",
        "unit__unit_type",
        "unit__floor_plan",
        "unit__unit_number",
    )
    filterset_class = LeaseFilters
    queryset = Lease.objects.for_current_user()
    serializer_class = LeaseSerialiserForStaff
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "Lease"

    def get_queryset(self):
        return (
            Lease.objects.for_current_user()
            .select_related(
                "resident",
                "resident__user",
                "unit",
                "parking_policy",
                "early_termination_policy",
                "additional_terms_policy",
                "pdf_asset",
            )
            .prefetch_related(
                "attachments",
                "esa_attachments",
                "late_fees",
                "other_occupants",
                "additional_signers",
                "pets_allowed",
                "utility_services",
                "one_time_fees",
            )
        )


class LeaseGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = Lease.objects.for_current_user()
    entity = "Lease"

    def get_serializer_class(self):
        if is_resident_request(self.request):
            return LeaseSerializerForResident
        return LeaseSerialiserForStaff


class LeaseCountView(CountAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = Lease.objects.for_current_user()
    entity = "Lease"

    @property
    def count_label_to_field_condition_map(self):
        return {
            "active": {
                "field": "status",
                "condition": {"status__in": ["active", "pending_renewal"]},
            },
            "pending": {"field": "status", "condition": {"status": "pending"}},
            "draft": {"field": "status", "condition": {"status": "draft"}},
            "past": {"field": "status", "condition": {"status": "terminated"}},
            "expired": {"field": "status", "condition": {"status": "expired"}},
        }


class LeaseLateFeesListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "daily_late_fee",
        "late_fee_limit_value",
    )
    filterset_fields = (
        "lease",
        "daily_late_fee_applicable",
        "daily_late_fee_applied_on",
        "late_fee_limit",
    )
    queryset = LeaseLateFees.objects.for_current_user()
    serializer_class = LeaseLateFeesSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseLateFees"


class LeaseLateFeesGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseLateFeesSerializer
    queryset = LeaseLateFees.objects.for_current_user()
    entity = "LeaseLateFees"


class LeaseOtherOccupantsListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "name",
        "relationship",
        "age",
    )
    filterset_fields = (
        "lease",
        "relationship",
    )
    queryset = LeaseOtherOccupants.objects.for_current_user()
    serializer_class = LeaseOtherOccupantsSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseOtherOccupants"


class LeaseOtherOccupantsGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseOtherOccupantsSerializer
    queryset = LeaseOtherOccupants.objects.for_current_user()
    entity = "LeaseOtherOccupants"


class LeaseAdditionalSignersListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "name",
        "email",
    )
    filterset_fields = ("lease",)
    queryset = LeaseAdditionalSigners.objects.for_current_user()
    serializer_class = LeaseAdditionalSignersSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseAdditionalSigners"


class LeaseAdditionalSignersGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseAdditionalSignersSerializer
    queryset = LeaseAdditionalSigners.objects.for_current_user()
    entity = "LeaseAdditionalSigners"


class LeasePetsAllowedListCreateView(StandardListCreateAPIMixin):
    search_fields = (
        "type_of_pet",
        "breed",
        "age",
    )
    filterset_fields = (
        "lease",
        "type_of_pet",
        "breed",
    )
    queryset = LeasePetsAllowed.objects.for_current_user()
    serializer_class = LeasePetsAllowedSerializer
    authentication_classes = [ResidentCompositeAuthentication]
    permission_classes = [
        HelixUserBasePermission
        | IsAuthenticatedResidentPermission
        | IsAuthenticatedHelixUser,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeasePetsAllowed"


class LeasePetsAllowedGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeasePetsAllowedSerializer
    queryset = LeasePetsAllowed.objects.for_current_user()
    entity = "LeasePetsAllowed"


class LeaseUtilityServicesListCreateView(StandardListCreateAPIMixin):
    filterset_fields = (
        "lease",
        "service",
        "responsible",
    )
    queryset = LeaseUtilityServices.objects.for_current_user()
    serializer_class = LeaseUtilityServicesSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseUtilityServices"


class LeaseUtilityServicesGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseUtilityServicesSerializer
    queryset = LeaseUtilityServices.objects.for_current_user()
    entity = "LeaseUtilityServices"


class LeaseOneTimeFeesListCreateView(StandardListCreateAPIMixin):
    filterset_fields = ("lease",)
    queryset = LeaseOneTimeFees.objects.for_current_user()
    serializer_class = LeaseOneTimeFeesSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseOneTimeFees"


class LeaseOneTimeFeesGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseOneTimeFeesSerializer
    queryset = LeaseOneTimeFees.objects.for_current_user()
    entity = "LeaseOneTimeFees"


class LeasePromotionalDiscountListCreateView(StandardListCreateAPIMixin):
    filterset_fields = ("lease",)
    queryset = LeasePromotionalDiscount.objects.for_current_user()
    serializer_class = LeasePromotionalDiscountSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeasePromotionalDiscount"


class LeasePromotionalDiscountGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeasePromotionalDiscountSerializer
    queryset = LeasePromotionalDiscount.objects.for_current_user()
    entity = "LeasePromotionalDiscount"


class LeaseKeysListCreateView(StandardListCreateAPIMixin):
    search_fields = ("copies",)
    filterset_fields = (
        "lease",
        "key_type",
    )
    queryset = LeaseKeys.objects.for_current_user()
    serializer_class = LeaseKeysSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "LeaseKeys"


class LeaseKeysGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseKeysSerializer
    queryset = LeaseKeys.objects.for_current_user()
    entity = "LeaseKeys"


class MoveRequestListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = MoveRequest.objects.for_current_user()
    serializer_class = MoveRequestSerializer
    entity = "MoveRequest"
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__unit_number",
    )
    filterset_class = MoveRequestFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-created_on"]


class MoveRequestMinimalListView(StandardListAPIMixin):
    """
    Minimal move request list API
    """

    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = MoveRequestMinimalSerializer
    entity = "MoveRequest"
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__unit_number",
    )
    filterset_class = MoveRequestFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-created_on"]

    def get_queryset(self):
        return MoveRequest.objects.for_current_user().select_related(
            "resident__user",
            "resident__user__profile_img",
            "unit__floor__building__location__property",
        )


class MoveRequestDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = MoveRequestSerializer
    queryset = MoveRequest.objects.for_current_user()
    entity = "MoveRequest"


class MoveRequestCountView(CountAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = MoveRequest.objects.for_current_user()
    entity = "MoveRequest"
    count_label_to_field_condition_map = {
        "all": {
            "field": "id",
            "condition": {},
        },
        "pending": {"field": "id", "condition": {"status": "pending"}},
        "awaiting_approval": {
            "field": "id",
            "condition": {"status": "awaiting_approval"},
        },
        "completed": {"field": "id", "condition": {"status": "completed"}},
        "cancelled": {"field": "id", "condition": {"status": "cancelled"}},
    }


class PropertyDetailAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True}
    entity = "Lease"

    def get_queryset(self):
        return (
            Lease.objects.for_current_user()
            .select_related(
                "resident",
                "resident__user",
                "unit",
                "unit__floor",
                "unit__floor__building",
                "unit__floor__building__location",
                "unit__floor__building__location__property",
                "parking_policy",
                "early_termination_policy",
                "additional_terms_policy",
            )
            .prefetch_related(
                "other_residents",
                "other_residents__user",
                "attachments",
                "esa_attachments",
            )
        )

    def get_serializer_class(self):
        return PropertyDetailSerializer


class MoveRequestInspectionListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    queryset = MoveInspectionLog.objects.for_current_user()
    serializer_class = MoveRequestInspectionLogSerializer
    entity = "MoveInspectionLog"
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-created_on"]


class MoveRequestInspectionDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = MoveRequestInspectionLogSerializer
    queryset = MoveInspectionLog.objects.for_current_user()
    entity = "MoveInspectionLog"


class ApplicationVIewDetailUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "patch": True}
    queryset = Application.objects.for_current_user()
    serializer_class = ApplicationVIewSerializer
    entity = "Application"


class LeaseListCreateViewV2(StandardListCreateAPIMixin):
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
        "unit__display_id",
        "unit__unit_type",
        "unit__floor_plan",
        "unit__unit_number",
    )
    filterset_class = LeaseFilters
    serializer_class = LeaseSerializerV2
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True}
    entity = "Lease"

    def get_queryset(self):
        return (
            Lease.objects.for_current_user()
            .select_related(
                "resident",
                "resident__user",
                "unit",
                "unit__floor",
                "unit__floor__building",
                "unit__floor__building__location",
                "unit__floor__building__location__property",
            )
            .prefetch_related("additional_signers")
        )


class LeaseGetUpdateViewV2(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True}
    serializer_class = LeaseSerializerV2
    entity = "Lease"

    def get_queryset(self):
        return (
            Lease.objects.for_current_user()
            .select_related(
                "resident",
                "resident__user",
                "unit",
                "unit__floor",
                "unit__floor__building",
                "unit__floor__building__location",
                "unit__floor__building__location__property",
            )
            .prefetch_related("additional_signers")
        )
