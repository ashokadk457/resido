import time
import jwt

from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from common.constants import (
    GUEST_PATIENT_TOKEN_EXPIRY,
    CreatePatientContexts,
    ALLOWED_METHODS_TO_PATIENT,
)
from common.errors import ERROR_DETAILS
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardListAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    CountAPIMixin,
)
from common.response import StandardAPIResponse
from common.helix_pagination import StandardPageNumberPagination
from common.exception import StandardAPIException
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.address_validator import AddressValidator
from common.utils.access_devices import (
    update_resident_device_access,
    is_within_lockout_duration,
)
from common.utils.general import is_valid_uuid
from helixauth.authentication.composite.guest import (
    GuestCompositeAuthentication,
    ResidentCompositeAuthentication,
)
from helixauth.authentication.resident.reset_password import (
    ResidentResetPasswordAuthentication,
)
from helixauth.constants import UsernameType
from helixauth.managers.user.generic import HelixUserManager
from helixauth.serializers import HelixUserSerializer
from helixauth.token.resident.access import ResidentAccessToken
from helixauth.utils import identify_username_type
from helixauth.managers.verificationcode import VerificationCodeManager
from residents.filtersets import (
    ResidentFilter,
    ResidentDocumentFilter,
    ResidentEvictionFilter,
)
from residents.managers.access_log import ResidentAccessLogManager
from residents.managers.patient import ResidentManager
from residents.managers.patientfamily import PatientFamilyManager
from residents.managers.registered_device import ResidentRegisteredDeviceManager
from helixauth.authentication.resident.rental_request import (
    ResidentRentalRequestAuthentication,
)
from helixauth.authentication.kc import KeyCloakAuthentication
from residents.models import (
    Resident,
    EmergencyContact,
    ResidentAddress,
    ResidentCoOccupants,
    ResidentFinancialGurantors,
    ResidentDocument,
    ResidentEviction,
)
from lease.models import Lease
from lease.serializers import RenterRentedPropertiesSerializer
from common.utils.logging import logger
from residents.serializers import (
    EmergencyContactSerializer,
    ResidentSerializer,
    PublicResidentSerializer,
    ResidentFamilySerializer,
    PatientAccessLogSerializer,
    PatientRegisteredDeviceSerializer,
    ResidentAddressSerializer,
    ResidentFinancialGurantorsSerializer,
    ResidentCoOccupantsSerializer,
    RenterProfileSerializer,
    ResidentDocumentSerializer,
    ResidentEvictionSerializer,
)
from lease.utils.pending_email import send_pending_application_emails


class PatientAuthMixin:
    @staticmethod
    def get_final_login_response(patient, user, user_tokens):
        patient_response_data = ResidentSerializer(instance=patient).data
        user_response_data = HelixUserSerializer(instance=user).data
        return {
            "user": user_response_data,
            "patient": patient_response_data,
            "user_tokens": user_tokens,
        }


class ResidentListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "id",
        "user__first_name",
        "user__last_name",
        "user__date_of_birth",
        "user__city",
        "user__state",
        "user__zipcode",
        "user__email",
        "user__phone",
    )
    filterset_class = ResidentFilter
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "Resident"

    def get_serializer_class(self):
        if self.request.user.is_authenticated:
            return ResidentSerializer
        return PublicResidentSerializer

    def get_queryset(self):
        return Resident.objects.for_current_user().order_by("-created_on")

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated and not self.request.query_params:
            raise StandardAPIException(
                code="not_allowed",
                detail=ERROR_DETAILS["not_allowed"],
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return super().get(request, *args, **kwargs)


class ResidentCountAPIView(CountAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = Resident.objects.for_current_user()
    count_label_to_field_condition_map = {
        "active": {
            "field": None,
            "condition": lambda qs: qs.filter(
                Q(leases__status="active") | Q(user__status="APPROVED")
            ).distinct(),
        },
        "invitation_pending": {
            "field": "user__status",
            "condition": {"user__status": "PENDING"},
        },
        "pending": {
            "field": "leases__status",
            "condition": {"leases__status": "pending"},
        },
        "terminated": {
            "field": "leases__status",
            "condition": {"leases__status": "terminated"},
        },
        "eviction": {
            "field": "leases__status",
            "condition": {"leases__status": "eviction"},
        },
        "expired": {
            "field": "leases__status",
            "condition": {"leases__status": "expired"},
        },
        "inactive": {
            "field": "user__status",
            "condition": {"user__status": "INACTIVE"},
        },
    }
    entity = "Resident"

    def get_filtered_queryset(self, label):
        """
        Apply filter for a given label safely.
        Handles both dict-based conditions and callables.
        """
        if label not in self.count_label_to_field_condition_map:
            return self.queryset.none()  # fallback to empty queryset

        condition = self.count_label_to_field_condition_map[label]["condition"]
        if callable(condition):
            return condition(self.queryset)
        return self.queryset.filter(**condition)

    def get(self, request, *args, **kwargs):
        """
        Returns a dictionary with counts per label.
        """
        counts = {}
        for label in self.count_label_to_field_condition_map.keys():
            counts[label] = self.get_filtered_queryset(label).count()

        return Response(counts)


class ResidentLoginAPIView(generics.GenericAPIView, PatientAuthMixin):
    permission_classes = [
        AllowAny,
    ]

    @staticmethod
    def validate_otp_for_guest_login(request_data):
        verification_data = request_data.pop(
            "verification", VerificationCodeManager.EMPTY_VERIFICATION_DATA
        )
        if not VerificationCodeManager.is_code_valid(**verification_data):
            ids = verification_data.get("user_ids")
            if ids and ids[0]:
                patient = Resident.objects.filter(
                    Q(id=ids[0]) | Q(email=ids[0])
                ).first()
                if patient:
                    update_resident_device_access(
                        patient,
                        None,
                        request_data.get("device_detail", None),
                        request_data.get("location_detail", {}),
                    )
            raise StandardAPIException(
                code="invalid_otp",
                detail=ERROR_DETAILS["invalid_otp"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return request_data

    def perform_guest_login(self, request_data, tenant):
        username = request_data.get("username")
        username_type = identify_username_type(username=username)
        if not username or not username_type:
            raise StandardAPIException(
                code="invalid_username",
                detail=ERROR_DETAILS["invalid_username"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if username_type == UsernameType.EMAIL.value:
            request_data["email"] = username
        elif username_type == UsernameType.PHONE.value:
            request_data["phone"] = username

        request_data = self.validate_otp_for_guest_login(request_data=request_data)
        guest_patient = ResidentManager.get_guest_patient(
            email=username, phone_number=username
        )
        if not guest_patient:
            patient_manager = ResidentManager(patient_data=request_data)
            guest_patient, error = patient_manager.create_guest_patient()
            if error:
                raise StandardAPIException(
                    code=error,
                    detail=ERROR_DETAILS[error],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        guest_patient_token_expiry = int(time.time()) + GUEST_PATIENT_TOKEN_EXPIRY
        guest_patient_access_token = ResidentAccessToken.for_tenant_resident(
            tenant=tenant,
            resident=guest_patient,
            sub_token_type="guest_patient",
            expiry=guest_patient_token_expiry,
        )
        guest_patient.last_login = timezone.now()
        guest_patient.save()
        update_resident_device_access(
            guest_patient,
            None,
            device_detail={},
            location_detail={},
            jti=guest_patient_access_token["jti"],
            exp=guest_patient_access_token["exp"],
        )
        guest_patient = ResidentManager.get_by(id=guest_patient.id)
        response_data = {
            "guest_token": str(guest_patient_access_token),
            "patient": ResidentSerializer(instance=guest_patient).data,
        }
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        guest_login = request.data.get("guest_login", None)

        if guest_login:
            return self.perform_guest_login(
                request_data=request.data, tenant=request.tenant
            )

        username = request.data.get("username", None)
        password = request.data.get("password", None)
        if not username or not password:
            raise StandardAPIException(
                code="username_or_password_missing",
                detail=ERROR_DETAILS["username_or_password_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        resident = Resident.objects.filter(
            (Q(user__phone=username) | Q(user__email__iexact=username))
        ).first()
        if resident is None:
            raise StandardAPIException(
                code="resident_not_found",
                detail=ERROR_DETAILS["resident_not_found"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if resident and is_within_lockout_duration(resident):
            raise StandardAPIException(
                code="user_locked",
                detail=ERROR_DETAILS["user_locked"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = resident.user
        user_manager = HelixUserManager(
            user_obj=user, username=username, password=password
        )
        try:
            user_tokens = user_manager.login()
        except Exception as e:
            logger.info(f"Exception occurred during login: {str(e)}")

            update_resident_device_access(
                user=resident,
                refresh=None,
                device_detail=request.data.get("device_detail"),
                location_detail=request.data.get("location_detail", {}),
            )
            raise e

        resident.last_login = timezone.now()
        resident.save()
        update_resident_device_access(
            resident,
            user_tokens["refresh_token"],
            request.data.get("device_detail", None),
            request.data.get("location_detail", {}),
        )
        resident = ResidentManager.get_by(id=resident.id)
        final_response_data = self.get_final_login_response(
            patient=resident, user=resident.user, user_tokens=user_tokens
        )
        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class ResidentRefreshTokenAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get_patient_from_access_token(access_token):
        unverified_payload = jwt.decode(
            jwt=access_token, options={"verify_signature": False}
        )
        sub = unverified_payload["sub"]
        return ResidentManager.get_resident_by_auth_user_id(auth_user_id=sub)

    def _update_resident_device_access(
        self, fresh_tokens, device_detail, location_detail
    ):
        if not device_detail:
            return

        patient = self.get_patient_from_access_token(
            access_token=fresh_tokens.get("access_token")
        )
        if patient is None:
            return

        update_resident_device_access(
            user=patient,
            refresh=fresh_tokens.get("refresh_token"),
            device_detail=device_detail,
            location_detail=location_detail,
        )

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            raise StandardAPIException(
                code="refresh_token_missing",
                detail=ERROR_DETAILS["refresh_token_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_manager = HelixUserManager()
        fresh_tokens = user_manager.refresh(refresh_token=refresh_token, reformat=False)
        self._update_resident_device_access(
            fresh_tokens=fresh_tokens,
            device_detail=request.data.get("device_detail", None),
            location_detail=request.data.get("location_detail", {}),
        )
        fresh_tokens["authorization_token"] = fresh_tokens["access_token"]
        return StandardAPIResponse(status=status.HTTP_200_OK, data=fresh_tokens)


class ResidentResetPasswordAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentResetPasswordAuthentication]
    allowed_methods_to_resident = {
        **ALLOWED_METHODS_TO_PATIENT,
        "post": True,
    }

    @staticmethod
    def post(request, *args, **kwargs):
        patient_obj = request.user
        new_password = request.data.get("password")
        if not new_password:
            raise StandardAPIException(
                code="invalid_password",
                detail=ERROR_DETAILS["invalid_password"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_obj = patient_obj.user
        auth_user_id = user_obj.auth_user_id
        if not auth_user_id:
            raise StandardAPIException(
                code="cannot_reset_password_of_guest_patient",
                detail=ERROR_DETAILS["cannot_reset_password_of_guest_patient"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_manager = HelixUserManager(user_obj=user_obj, email=user_obj.email)
        user_manager.change_password(password=new_password, approve_if_pending=True)

        update_resident_device_access(
            user=patient_obj,
            refresh=None,
            device_detail=request.data.get("device_detail", None),
            location_detail=request.data.get("location_detail", {}),
        )

        # Send pending application emails after successful password setup
        send_pending_application_emails(patient_obj)

        final_response_data = {"password_reset": True}
        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class ResidentDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    authentication_classes = [
        KeyCloakAuthentication,
        ResidentRentalRequestAuthentication,
    ]
    allowed_methods_to_resident = {"patch": True, "get": True}
    queryset = Resident.objects.for_current_user()
    serializer_class = ResidentSerializer
    entity = "Resident"


class AddressValidation(APIView):
    def post(self, request):
        req = request.data
        fields = ["address1", "address2", "city", "state", "zip"]
        for field in fields:
            if field not in req:
                return Response(
                    {"error": "Required paramter is missing or invalid."}, status=400
                )
        res = AddressValidator().validate(
            req["address1"], req["address2"], req["city"], req["state"], req["zip"]
        )
        return Response(res, content_type="application/json")


class EmergencyContactCreate(StandardListCreateAPIMixin):
    serializer_class = EmergencyContactSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "post": True}
    entity = "EmergencyContact"

    def get_queryset(self):
        queryset = EmergencyContact.objects.for_current_user()
        return queryset


class EmergencyContactDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "patch": True, "put": True}
    entity = "EmergencyContact"
    queryset = EmergencyContact.objects.for_current_user()
    serializer_class = EmergencyContactSerializer


class ResidentsFamilyCreateListAPIView(APIView):
    permission_classes = [IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True, "post": True}

    @staticmethod
    def _create_family_obj(family_data, patient, relationship, tenant):
        family_serializer = ResidentFamilySerializer(
            data=family_data,
            context={
                "tenant": tenant,
                "context": CreatePatientContexts.book_appointment.value,
                "proxy": False,
                "proxy_patient": patient,
                "proxy_patient_relationship": relationship,
            },
        )
        family_serializer.is_valid(raise_exception=True)

        family, _ = family_serializer.save()
        return family

    def post(self, request):
        patient = request.patient
        family_data = request.data.pop("family", {})
        relationship = request.data.pop("relationship", None)
        tenant = request.tenant
        return self._post(
            patient=patient,
            family_data=family_data,
            relationship=relationship,
            tenant=tenant,
        )

    def _post(self, patient, family_data, relationship, tenant):
        if not relationship or not family_data:
            raise StandardAPIException(
                code="relation_or_family_missing",
                detail=ERROR_DETAILS["relation_or_family_missing"],
                status_code=status.HTTP_403_FORBIDDEN,
            )
        family = self._create_family_obj(family_data, patient, relationship, tenant)
        obj, _ = ResidentManager.create_patient_family_relation(
            patient, family, relationship
        )
        resp_data = ResidentFamilySerializer(
            instance=family, context={"relationship": relationship, "family_id": obj.id}
        ).data
        return StandardAPIResponse(data=resp_data, status=status.HTTP_200_OK)

    def _get(self, patient):
        family_objs = PatientFamilyManager.get_patient_family_relations(patient)
        resp_data = [
            ResidentFamilySerializer(
                instance=obj.member,
                context={"relationship": obj.relationship, "family_id": obj.id},
            ).data
            for obj in family_objs
        ]
        return StandardAPIResponse(data=resp_data, status=status.HTTP_200_OK)

    def get(self, request):
        patient = request.patient
        return self._get(patient=patient)


class ResidentRegisteredDevicesAPIView(generics.ListAPIView):
    authentication_classes = [GuestCompositeAuthentication]
    serializer_class = PatientRegisteredDeviceSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "PatientRegisteredDevice"

    def list(self, request, *args, **kwargs):
        try:
            resident = request.user.resident
            queryset = ResidentRegisteredDeviceManager().get_all_active_registered_devices_of_user(
                resident
            )
        except Resident.DoesNotExist:
            # User is not a resident (e.g., staff user), return empty device list
            queryset = []

        serializer = self.get_serializer(queryset, many=True)
        return StandardAPIResponse(
            data={"devices": serializer.data}, status=status.HTTP_200_OK
        )


class ResidentAccessLogAPIView(generics.ListAPIView):
    authentication_classes = [GuestCompositeAuthentication]
    serializer_class = PatientAccessLogSerializer
    pagination_class = StandardPageNumberPagination
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "PatientAccessLog"

    def get_queryset(self):
        try:
            resident = self.request.user.resident
            return (
                ResidentAccessLogManager()
                .filter_by(user=resident)
                .order_by("-updated_on")
            )
        except Resident.DoesNotExist:
            # User is not a resident (e.g., staff user), return empty queryset
            return ResidentAccessLogManager().filter_by(user__isnull=True)


class ResidentLogoutRegisteredDevicesAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    # entity is not required as every user will have access to this and this can not be controlled by module
    # entity = "PatientRegisteredDevice"

    def post(self, request, *args, **kwargs):
        # TODO MUST Later adjust this with KC based Tokens. For KC, need to check to close individual session ids
        try:
            resident = request.user.resident
        except Resident.DoesNotExist:
            # User is not a resident (e.g., staff user), no devices to logout
            return StandardAPIResponse(status=status.HTTP_202_ACCEPTED)

        data = request.data
        device_manager = ResidentRegisteredDeviceManager()
        if data.get("all", False):
            devices = device_manager.filter_by(user=resident, active=True)
        elif data.get("device_id"):
            devices = device_manager.filter_by(
                user=resident, id=data.get("device_id"), active=True
            )
        else:
            raise StandardAPIException(
                code="logout_device_required_missing",
                detail=ERROR_DETAILS["logout_device_required_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not devices.exists():
            return StandardAPIResponse(status=status.HTTP_202_ACCEPTED)

        for device in devices:
            all_token_tuples = list(
                ResidentAccessLogManager().get_all_active_tokens_for_device(
                    resident, device
                )
            )
            user_manager = HelixUserManager()
            user_manager.logout_tokens(refresh_token_tuples=all_token_tuples)
            device_manager.deactivate_device(device)

        return StandardAPIResponse(status=status.HTTP_202_ACCEPTED)


class ResidentUnlockAPIView(APIView):
    module = "users"
    module_action = "can_update"
    swagger_schema = None
    permission_classes = [HelixUserBasePermission]
    entity = "Resident"

    def post(self, request, *args, **kwargs):
        patient_id = kwargs.get("pk")
        patient = Resident.objects.filter(id=patient_id).first()
        if not patient or not patient.locked:
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        patient.locked = False
        patient.failed_attempt_count = 0
        patient.save()
        return StandardAPIResponse(
            {
                "status": "success",
                "code": "success",
                "message": "successfully unlocked the patient",
            },
            status=status.HTTP_200_OK,
        )


class ResidentAddressListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ResidentAddressSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [
        KeyCloakAuthentication,
        ResidentRentalRequestAuthentication,
    ]
    allowed_methods_to_resident = {"post": True, "get": True}
    entity = "ResidentAddress"
    queryset = ResidentAddress.objects.for_current_user()
    filterset_fields = (
        "resident",
        "is_primary",
        "country",
        "state",
    )


class ResidentAddressDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [
        KeyCloakAuthentication,
        ResidentRentalRequestAuthentication,
    ]
    allowed_methods_to_resident = {"patch": True, "get": True}
    entity = "ResidentAddress"
    queryset = ResidentAddress.objects.for_current_user()
    serializer_class = ResidentAddressSerializer


class ResidentCoOccupantsListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ResidentCoOccupantsSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentCoOccupants"
    queryset = ResidentCoOccupants.objects.for_current_user()
    filterset_fields = (
        "include_in_notice",
        "resident",
        "country",
        "state",
    )


class ResidentCoOccupantsDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentCoOccupants"
    queryset = ResidentCoOccupants.objects.for_current_user()
    serializer_class = ResidentCoOccupantsSerializer


class ResidentFinancialGurantorsListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ResidentFinancialGurantorsSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentFinancialGurantors"
    queryset = ResidentFinancialGurantors.objects.for_current_user()
    filterset_fields = (
        "include_in_notice",
        "is_primary",
        "country",
        "resident",
        "state",
    )


class ResidentFinancialGurantorsDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentFinancialGurantors"
    queryset = ResidentFinancialGurantors.objects.for_current_user()
    serializer_class = ResidentFinancialGurantorsSerializer


class RenterRentedPropertiesAPIView(StandardListAPIMixin):
    """
    API endpoint to list all rented properties for a resident.
    Supports filtering by status, ordering by date and rent, and pagination.
    """

    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "Lease"
    serializer_class = RenterRentedPropertiesSerializer
    pagination_class = StandardPageNumberPagination
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    filterset_fields = ("status",)
    ordering_fields = ("start_date", "end_date", "rent_amount")

    def get_queryset(self):
        """Get rented properties for the specified resident"""
        resident_id = self.kwargs.get("pk")
        return (
            Lease.objects.filter(resident_id=resident_id)
            .select_related("unit__floor__building__location__property", "resident")
            .order_by("-start_date")
        )


class RenterProfileAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "Resident"
    queryset = Resident.objects.for_current_user()
    serializer_class = RenterProfileSerializer


class ResidentDocumentListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ResidentDocumentSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "post": True}
    entity = "ResidentDocument"
    queryset = ResidentDocument.objects.for_current_user()
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "front_image__filename",
        "back_image__filename",
        "resident__user__first_name",
        "resident__user__last_name",
    )
    filterset_class = ResidentDocumentFilter


class ResidentDocumentDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    allowed_methods_to_resident = {"get": True, "patch": True, "put": True}
    entity = "ResidentDocument"
    queryset = ResidentDocument.objects.for_current_user()
    serializer_class = ResidentDocumentSerializer


class ResidentEvictionListCreateAPIView(StandardListCreateAPIMixin):
    serializer_class = ResidentEvictionSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentEviction"
    queryset = ResidentEviction.objects.for_current_user()
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "resident__user__first_name",
        "resident__user__last_name",
    )
    filterset_class = ResidentEvictionFilter


class ResidentEvictionDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "ResidentEviction"
    queryset = ResidentEviction.objects.for_current_user()
    serializer_class = ResidentEvictionSerializer


class ResidentInvitationAPIView(GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Resident"

    def post(self, request, *args, **kwargs):
        ids = request.data.get("resident_ids", [])
        if not ids:
            raise StandardAPIException(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param="resident_ids"
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        is_valid_ids = all([True if is_valid_uuid(i) else False for i in ids])
        if not is_valid_ids:
            raise StandardAPIException(
                code="invalid_value",
                detail=ERROR_DETAILS["invalid_value"].format(attr="resident_ids"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        objs = Resident.objects.for_current_user().filter(id__in=ids)
        if not objs.exists():
            raise StandardAPIException(
                code="invalid_renter_id",
                detail=ERROR_DETAILS["invalid_renter_id"].format(obj_type="Resident"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        sent_to = []
        for obj in objs:
            try:
                ResidentManager.send_email(obj)
                sent_to.append(obj.user.email)
            except Exception as e:
                logger.error(f"Error resending email: {str(e)}")

        return StandardAPIResponse(data={"sent_to": sent_to}, status=status.HTTP_200_OK)
