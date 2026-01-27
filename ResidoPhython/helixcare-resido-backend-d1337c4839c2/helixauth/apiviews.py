import time
import json
import django_filters

from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import update_last_login
from django.core.exceptions import ValidationError
from django.db.models import Q, Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, views, status, filters
from helixauth.token.user.access import HelixUserAccessToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import common.helix_permissions as helix_permission
from common.constants import (
    RESET_PASSWORD_TOKEN_EXPIRY,
    OTP_EXPIRY_IN_SECONDS,
)
from notifications.constants import TemplateCode
from notifications.managers.notificationqueue import NotificationQueueManager
from staff.constants import CareCenterRoleType
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.constants import ALLOWED_METHODS_TO_PATIENT
from common.helix_pagination import (
    LargeResultsSetPagination,
    StandardPageNumberPagination,
)
from common.response import StandardAPIResponse
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    StandardListAPIMixin,
)
from common.utils.datetime import DateTimeUtils
from common.utils.general import is_valid_uuid
from common.utils.logging import logger
from common.utils.access_devices import is_within_lockout_duration, update_device_access
from helixauth.constants import AuthenticateType, DEFAULT_COUNTRY_CODE
from helixauth.managers.admin import AdminManager
from helixauth.managers.verificationcode import VerificationCodeManager
from helixauth.models import (
    SecurityQuestion,
    HelixUser,
    ModulePermission,
    UserRole,
    Module,
    Entity,
    UserGroup,
    ModuleComposition,
    SubModulePermission,
    EntityAttributePermission,
    Policy,
    PolicyVersion,
    UserPolicyAcceptance,
)
from lease.models import Lease
from lease.constants import LeaseStatus
from helixauth.serializers import (
    CustomTokenRefreshSerializer,
    SecurityQuestionSerializer,
    UserSerializer,
    HelixUserSerializer,
    ModulePermissionSerializer,
    ModuleSerializer,
    UserRoleCreateSerializer,
    UserGroupExtendedSerializer,
    ModuleCompositionSerializer,
    RegisteredDeviceSerializer,
    AccessLogSerializer,
    AuthenticateSerializer,
    UserGroupSerializer,
    UserRoleDetailSerializer,
    SubmodulePermissionSerializer,
    EntityAttributePermissionSerializer,
    ModulePermissionDetailSerializer,
    ModulePermissionReadOnlySerializer,
    SubmodulePermissionReadOnlySerializer,
    EntitySerializer,
    CareCenterRoleSerializer,
    PolicyListSerializer,
    PolicyDetailSerializer,
    UserPolicyAcceptanceSerializer,
)
from helixauth.managers.registered_device import RegisteredDeviceManager
from helixauth.managers.access_log import AccessLogManager
from helixauth.managers.user.generic import HelixUserManager
from helixauth.managers.user.object import HelixUserObjectManager
from helixauth.utils import (
    send_otp,
    send_reset_password_link_to_helix_user,
    send_temp_password_email,
    random_password,
)
from residents.models import Resident
from lease.models import Application
from lease.constants import LeaseApplicationStatus
from staff.models import HelixStaff
from staff.serializers import TenantAdminSerializer
from helixauth.token.resident.access import ResidentAccessToken
from helixauth.authentication.kc import KeyCloakAuthentication
from helixauth.authentication.user.reset_password import (
    UserResetPasswordAuthentication,
)
from common.permissions import IsAuthenticatedHelixUser
from .utils import (
    get_token_for_user,
    get_user,
    get_resident_or_staff_by_user,
    get_users,
)
from lease.utils.pending_email import send_pending_application_emails


def change_password(
    user, password, old_password=None, device_detail={}, location_detail={}
):
    if old_password and not user.check_password(old_password):
        raise StandardAPIException(
            code="incorrect_password",
            detail="Old password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not user or user.is_anonymous:
        raise StandardAPIException(
            code="anonymous_access",
            detail="Anonymous access denied",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    elif not password:
        raise StandardAPIException(
            code="no_password",
            detail="No Password",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    elif user.check_password(password):
        raise StandardAPIException(
            code="duplicate_password",
            detail=ERROR_DETAILS["duplicate_password"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if is_within_lockout_duration(user):
        return StandardAPIException(
            code="user_locked",
            detail=ERROR_DETAILS["user_locked"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_password(password, user)
    except ValidationError as e:
        update_device_access(user, None, device_detail, location_detail)
        if user.locked:
            raise StandardAPIException(
                code="user_locked",
                detail=ERROR_DETAILS["user_locked"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        raise StandardAPIException(
            code="invalid_password",
            detail=(
                json.dumps(e.messages)
                if hasattr(e, "messages") and e.messages
                else ERROR_DETAILS["invalid_password"]
            ),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user_manager = HelixUserManager(user_obj=user, email=user.email, password=password)
    user_manager.change_password(password=password, approve_if_pending=True)
    fresh_tokens = user_manager.login()
    (
        associated_account,
        account_class_name,
    ) = user_manager.get_associated_patient_or_provider()
    _id = None if associated_account is None else str(associated_account.id)
    _type = None if associated_account is None else account_class_name

    data = {
        "status": "success",
        "message": "Password set successfully",
        "token": fresh_tokens.get("access_token"),
        "expires_in": DateTimeUtils.get_iso_datetime_from_now(
            offset_in_seconds=fresh_tokens["expires_in"]
        ),
        "refresh": fresh_tokens.get("refresh_token"),
        "user_id": str(user.id),
        "id": _id,
        "type": _type,
    }
    update_device_access(
        user, fresh_tokens["refresh_token"], device_detail, location_detail
    )
    update_last_login(None, user)
    return Response(data)


class ChangePassword(views.APIView):
    """
    It takes auth token key and new password as the input
    """

    permission_classes = [HelixUserBasePermission]
    authentication_classes = [KeyCloakAuthentication]
    entity = "HelixStaff"

    def post(self, request):
        user_id = request.data.get("user_id")
        if not is_valid_uuid(user_id):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = get_user(user_id)
        if not user:
            return Response(
                {"message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return change_password(
            user,
            request.data.get("new_password"),
            request.data.get("old_password"),
            request.data.get("device_detail", {}),
            request.data.get("location_detail", {}),
        )


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeyCloakAuthentication]

    @staticmethod
    def post(request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise StandardAPIException(
                code="refresh_token_missing",
                detail=ERROR_DETAILS["refresh_token_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_manager = HelixUserManager(user_obj=request.user)
        user_manager.logout(refresh_token=refresh_token)

        return StandardAPIResponse(data=None, status=status.HTTP_200_OK)


class ResetPassword(views.APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not is_valid_uuid(user_id):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = get_user(user_id)
        if not user:
            return Response(
                {"message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # Generate Event
        send_otp(user.helixuser_staff, "EMAIL")
        return Response(
            {
                "message": "Password reset request has been registerd",
                "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
            status=status.HTTP_201_CREATED,
        )


class ResetPasswordLink(views.APIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "HelixStaff"

    def post(self, request):
        user_id = request.data.get("user_id")
        if not is_valid_uuid(user_id):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = get_user(user_id)
        if not user:
            return Response(
                {"message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # Generate Event
        send_reset_password_link_to_helix_user(user.helixuser_staff, "EMAIL")
        return Response(
            {
                "message": "Password reset link has been sent",
                "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
            status=status.HTTP_201_CREATED,
        )


class TemporaryPasswordView(generics.GenericAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "HelixStaff"

    @staticmethod
    def set_random_password(user):
        temporary_password = random_password()
        user_manager = HelixUserManager(user_obj=user)
        return (
            user_manager.change_password(password=temporary_password),
            temporary_password,
        )

    def post(self, request):
        user_id = request.data.get("user_id")
        if not is_valid_uuid(user_id):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user = get_user(user_id)
        if not user:
            return Response(
                {"message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user, temporary_password = self.set_random_password(user=user)
        send_temp_password_email(
            user=user.helixuser_staff, temporary_password=temporary_password
        )
        return Response(
            {
                "message": "Temporary Password have been set and shared with user",
            },
            status=status.HTTP_201_CREATED,
        )


class SecurityQuestionView(generics.ListAPIView):
    serializer_class = SecurityQuestionSerializer
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        queryset = SecurityQuestion.objects.filter(active=True)
        return queryset


class ConfirmResetPassword(views.APIView):
    """
    It takes reset key and new password as the input
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        user_id = request.data.get("user_id")
        if not is_valid_uuid(user_id):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = get_user(user_id)
        if not user:
            return Response(
                {"code": "invalid_data", "message": "Details provided is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not VerificationCodeManager.is_code_valid(
            user_ids=[user_id],
            user_type=request.data.get("user_type", 1),
            code=request.data.get("code"),
        ):
            raise StandardAPIException(
                code="invalid_request",
                detail=ERROR_DETAILS["invalid_request"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            response = change_password(
                user,
                request.data.get("password"),
                None,
                request.data.get("device_detail", {}),
                request.data.get("location_detail", {}),
            )

            # Send pending application emails after successful password setup
            send_pending_application_emails(user)

            return response
        except ValidationError:
            raise StandardAPIException(
                code="invalid_password",
                detail=ERROR_DETAILS["invalid_password"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class RegisterView(generics.CreateAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = HelixUser.objects.all()
    serializer_class = UserSerializer


class AuthenticateAPIView(generics.GenericAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = AuthenticateSerializer

    def post(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if type(e) is ValueError:
                data = e.args[0]
                if isinstance(data, dict):
                    return StandardAPIResponse(
                        data={
                            "message": ERROR_DETAILS[data.get("code")],
                            **data,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                raise StandardAPIException(
                    code=data,
                    detail=ERROR_DETAILS[data],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            raise e

        return StandardAPIResponse(serializer.validated_data, status=status.HTTP_200_OK)


class LoginView(AuthenticateAPIView):
    def post(self, request, format=None):
        request.data["type"] = AuthenticateType.login_with_password.value
        return super().post(request, format)


class TestAuthenticateAPIView(APIView):
    authentication_classes = [KeyCloakAuthentication]

    def get(self, request):
        current_user = self.request.user
        data = HelixUserSerializer(current_user).data
        return StandardAPIResponse(data, status=status.HTTP_200_OK)


class ValidateOTPAndLogin(AuthenticateAPIView):
    def post(self, request):
        request.data["type"] = AuthenticateType.login_with_otp.value
        return super().post(request, format)


# class ActivateUserViaOTP(AuthenticateAPIView):
#     def post(self, request, format=None):
#         request.data["type"] = AuthenticateType.validate_otp.value
#         return super().post(request, format)


class CustomTokenRefreshView(AuthenticateAPIView):
    authentication_classes = [KeyCloakAuthentication]
    serializer_class = CustomTokenRefreshSerializer


class ValidateSecurityQuestionAndLogin(AuthenticateAPIView):
    def post(self, request, format=None):
        request.data["type"] = AuthenticateType.validate_security_question.value
        return super().post(self, request, format)


class ActivateUser(AuthenticateAPIView):
    def post(self, request, format=None):
        request.data["type"] = AuthenticateType.activate_and_authenticate.value
        return super().post(self, request, format)


class UserRoleView(APIView):
    def get(self, request, pk):
        match = None
        try:
            match = HelixStaff.objects.get(id=pk)
        except HelixStaff.DoesNotExist:
            pass
        if match is None:
            try:
                match = Resident.objects.get(id=pk)
            except Resident.DoesNotExist:
                pass
        if match is not None:
            permission = helix_permission.get_user_permissions(match.user)
            perm_tuple = [(x.name) for x in permission]
            groups = helix_permission.get_user_group(match.user)
            group_tuple = [(x.name) for x in groups]
            return Response({"permissions": perm_tuple, "groups": group_tuple})
        else:
            return Response({"message": "Invalid ID!"}, status=400)


class CreateTenantAdmin(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        if "email" not in request.data:
            raise StandardAPIException(
                code="email_missing",
                detail=ERROR_DETAILS["email_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        TenantAdminSerializer(data=request.data).is_valid(raise_exception=True)
        provider = AdminManager().create_tenant_admin(request.data["email"])
        if not provider.user.is_active:
            try:
                send_otp(provider, "EMAIL")
            except Exception as e:
                logger.error(f"Error occurred while sending otp email: {e}")
                raise StandardAPIException(
                    code="email_error",
                    detail=ERROR_DETAILS["email_error"],
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            raise StandardAPIException(
                code="user_already_verified",
                detail=ERROR_DETAILS["user_already_verified"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        return StandardAPIResponse(
            data={
                "provider": TenantAdminSerializer(provider).data,
                "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
            status=status.HTTP_200_OK,
        )


class ActivateUserViaOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        if not request.data.get("email"):
            raise StandardAPIException(
                code="email_missing",
                detail=ERROR_DETAILS["email_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not request.data.get("otp"):
            raise StandardAPIException(
                code="otp_missing",
                detail=ERROR_DETAILS["otp_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            provider = AdminManager().validate_otp_and_activate_user(
                request.data["email"], request.data["otp"], request.data
            )
            if provider:
                token = get_token_for_user(provider.user)
                update_device_access(
                    provider.user,
                    token["refresh"],
                    request.data.get("device_detail", {}),
                    request.data.get("location_detail", {}),
                )
                update_last_login(None, provider.user)
                return StandardAPIResponse(
                    data={
                        "provider": TenantAdminSerializer(provider).data,
                        "token": token,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                if provider:
                    update_device_access(
                        provider.user,
                        None,
                        request.data.get("device_detail", {}),
                        request.data.get("location_detail", {}),
                    )
                    if provider.user.locked:
                        raise StandardAPIException(
                            code="user_locked",
                            detail=ERROR_DETAILS["user_locked"],
                            status_code=status.HTTP_400_BAD_REQUEST,
                        )
                raise StandardAPIException(
                    code="invalid_otp",
                    detail=ERROR_DETAILS["invalid_otp"],
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )
        except HelixStaff.DoesNotExist:
            raise StandardAPIException(
                code="no_active_user",
                detail=ERROR_DETAILS["no_active_user"],
                status_code=status.HTTP_404_NOT_FOUND,
            )


class HelixUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    queryset = HelixUser.objects.all()
    serializer_class = HelixUserSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    pagination_class = LargeResultsSetPagination
    search_fields = ("first_name", "last_name", "city", "state", "zipcode")
    filter_fields = (
        "first_name",
        "last_name",
        "city",
        "state",
        "zipcode",
        "gender",
    )
    ordering_fields = (
        "first_name",
        "last_name",
        "status",
    )
    entity = "HelixStaff"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        response_data = (
            {
                "values": serializer.data,
                "pagination": {
                    "page": self.request.query_params.get("page", 1),
                    "per_page": self.request.query_params.get(
                        "page_size", self.pagination_class.page_size
                    ),
                    "more": self.get_paginated_response(serializer.data).data.get(
                        "next"
                    )
                    is not None,
                    "total": queryset.count(),
                },
            },
        )

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return StandardAPIResponse(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        return StandardAPIResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class HelixUserDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = HelixUserSerializer
    queryset = HelixUser.objects.all()
    entity = "HelixStaff"

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except HelixUser.DoesNotExist:
            raise StandardAPIException(
                code="user_not_found",
                detail=ERROR_DETAILS["user_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)
        return StandardAPIResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class UserGroupListCreateView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["name"]
    filterset_fields = ["name", "is_active"]
    allowed_methods_to_resident = {"get": True}
    entity = "UserGroup"


class UserGroupGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    allowed_methods_to_resident = {"get": True}
    entity = "UserGroup"


class UserRoleListCreateView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    queryset = UserRole.objects.all().select_related("group")
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "role_name",
        "group__name",
    )
    pagination_class = None
    filter_fields = ("is_role_active", "seeded")
    ordering_fields = ("group__name",)
    allowed_methods_to_resident = {"get": True}
    entity = "UserRole"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserRoleCreateSerializer
        return UserGroupExtendedSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        groups = {}
        for i in queryset:
            if not groups.get(str(i.group.id)):
                setattr(i.group, "c_roles", [])
                groups[str(i.group.id)] = i.group
            getattr(groups[str(i.group.id)], "c_roles").append(i)
        serializer = self.get_serializer(list(groups.values()), many=True)
        return Response(serializer.data)


class UserRoleRetrieveUpdateView(StandardRetrieveUpdateAPIMixin):
    queryset = UserRole.objects.all().prefetch_related(
        "permissions",
        "permissions__module",
    )
    serializer_class = UserRoleDetailSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "UserRole"


class UserRoleModulePermissionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    serializer_class = ModulePermissionDetailSerializer
    entity = "ModulePermission"

    def get_queryset(self):
        return (
            ModulePermission.objects.filter(
                role_id=self.kwargs.get("role_id"),
            )
            .select_related("module")
            .prefetch_related("module__submodules", "module__submodules__permissions")
        )


class UserRoleEntityPermissionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    queryset = Entity.objects.all().prefetch_related(
        "attributes", "attributes__permissions"
    )
    serializer_class = EntitySerializer
    entity = "Entity"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if not hasattr(self, "role"):
            try:
                self.role = UserRole.objects.get(id=self.kwargs.get("role_id"))
            except Exception:
                raise StandardAPIException(
                    code="invalid_id",
                    detail=ERROR_DETAILS["invalid_id"].format(param="role"),
                    status_code=status.HTTP_404_NOT_FOUND,
                )
        context["role"] = self.role
        return context


class ModuleListView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    pagination_class = LargeResultsSetPagination
    search_fields = ("product", "code", "name")
    filter_fields = ("product", "code", "name", "is_active")
    ordering_fields = (
        "product",
        "code",
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        response_data = (
            {
                "values": serializer.data,
                "pagination": {
                    "page": self.request.query_params.get("page", 1),
                    "per_page": self.request.query_params.get(
                        "page_size", self.pagination_class.page_size
                    ),
                    "more": self.get_paginated_response(serializer.data).data.get(
                        "next"
                    )
                    is not None,
                    "total": queryset.count(),
                },
            },
        )

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class ModuleRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Module.DoesNotExist:
            raise StandardAPIException(
                code="module_not_found",
                detail=ERROR_DETAILS["module_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        response_data = serializer.data
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)
        return StandardAPIResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class ModuleCompositionListView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = ModuleComposition.objects.all()
    serializer_class = ModuleCompositionSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    pagination_class = LargeResultsSetPagination
    search_fields = ("module", "entity")
    filter_fields = ("module", "entity")
    ordering_fields = (
        "module",
        "entity",
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        response_data = (
            {
                "values": serializer.data,
                "pagination": {
                    "page": self.request.query_params.get("page", 1),
                    "per_page": self.request.query_params.get(
                        "page_size", self.pagination_class.page_size
                    ),
                    "more": self.get_paginated_response(serializer.data).data.get(
                        "next"
                    )
                    is not None,
                    "total": queryset.count(),
                },
            },
        )

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class ModuleCompositionRetrieveView(generics.RetrieveAPIView):
    queryset = ModuleComposition.objects.all()
    serializer_class = ModuleCompositionSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ModuleComposition.DoesNotExist:
            raise StandardAPIException(
                code="module_composition_not_found",
                detail=ERROR_DETAILS["module_composition_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        response_data = serializer.data
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class SubmodulePermissionListView(StandardListAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "SubModulePermission"
    queryset = SubModulePermission.objects.all()
    serializer_class = SubmodulePermissionSerializer
    search_fields = ("submodule__module", "submodule__submodule", "role")
    filter_fields = (
        "is_active",
        "role",
    )


class SubmodulePermissionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "SubModulePermission"
    queryset = SubModulePermission.objects.all()
    serializer_class = SubmodulePermissionSerializer


class EntityAttributePermissionListView(StandardListAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "EntityAttributePermission"
    queryset = EntityAttributePermission.objects.all()
    serializer_class = EntityAttributePermissionSerializer
    search_fields = ("attribute__attribute", "attribute__entity", "role")
    filter_fields = ("role",)


class EntityAttributePermissionGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "EntityAttributePermission"
    queryset = EntityAttributePermission.objects.all()
    serializer_class = EntityAttributePermissionSerializer


class ModulePermissionListView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]
    queryset = ModulePermission.objects.all()
    serializer_class = ModulePermissionSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    pagination_class = LargeResultsSetPagination
    search_fields = ("module", "role")
    filter_fields = (
        "module",
        "role",
        "can_create",
        "can_view",
        "can_update",
        "can_delete",
        "is_active",
    )
    ordering_fields = (
        "module",
        "role",
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)

        response_data = (
            {
                "values": serializer.data,
                "pagination": {
                    "page": self.request.query_params.get("page", 1),
                    "per_page": self.request.query_params.get(
                        "page_size", self.pagination_class.page_size
                    ),
                    "more": self.get_paginated_response(serializer.data).data.get(
                        "next"
                    )
                    is not None,
                    "total": queryset.count(),
                },
            },
        )

        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class ModulePermissionRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = ModulePermission.objects.all()
    serializer_class = ModulePermissionSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except ModulePermission.DoesNotExist:
            raise StandardAPIException(
                code="module_permission_not_found",
                detail=ERROR_DETAILS["module_permission_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(instance)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)
        return StandardAPIResponse(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class RegisteredDevicesAPIView(generics.ListAPIView):
    """Get registered devices - handles both /users/{id}/registered-devices and /registered-devices"""

    serializer_class = RegisteredDeviceSerializer
    permission_classes = [HelixUserBasePermission]
    entity = "HelixStaff"

    def list(self, request, *args, **kwargs):
        # Try to get user_id from URL kwargs first (for /users/{id}/registered-devices)
        user_id = kwargs.get("pk")

        if user_id:
            # User ID provided in URL - get that user
            user = HelixUser.objects.filter(id=user_id).first()
            if not user:
                raise StandardAPIException(
                    code="invalid_user_id",
                    detail=ERROR_DETAILS["invalid_user_id"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # No user ID in URL - use authenticated user from token (for /registered-devices)
            user = request.user
            if not user or not user.is_authenticated:
                raise StandardAPIException(
                    code="unauthorized",
                    detail="Authentication required",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

        queryset = RegisteredDeviceManager().get_all_active_registered_devices_of_user(
            user
        )
        serializer = self.get_serializer(queryset, many=True)
        return StandardAPIResponse(
            data={"devices": serializer.data}, status=status.HTTP_200_OK
        )


class AccessLogAPIView(generics.ListAPIView):
    """Get access logs - handles both /users/{id}/access-logs and /access-logs"""

    serializer_class = AccessLogSerializer
    pagination_class = StandardPageNumberPagination
    permission_classes = [HelixUserBasePermission]
    entity = "HelixStaff"

    def get_queryset(self):
        # Try to get user_id from URL kwargs first (for /users/{id}/access-logs)
        user_id = self.kwargs.get("pk")

        if not user_id:
            # No user ID in URL - use authenticated user from token (for /access-logs)
            user_id = self.request.user.id

        return AccessLogManager().filter_by(user_id=user_id).order_by("-updated_on")


class LogoutRegisteredDevicesAPIView(generics.GenericAPIView):
    """Logout device(s) - handles both /users/{id}/logout-device and /logout-device"""

    permission_classes = [HelixUserBasePermission]
    entity = "HelixStaff"

    def post(self, request, *args, **kwargs):
        # Try to get user_id from URL kwargs first (for /users/{id}/logout-device)
        user_id = kwargs.get("pk")

        if not user_id:
            # No user ID in URL - use authenticated user from token (for /logout-device)
            user_id = request.user.id

        data = request.data
        device_manager = RegisteredDeviceManager()
        if data.get("all", False):
            devices = device_manager.filter_by(user_id=user_id, active=True)
        elif data.get("device_id"):
            devices = device_manager.filter_by(
                user_id=user_id, id=data.get("device_id"), active=True
            )
        else:
            raise StandardAPIException(
                code="logout_device_required_missing",
                detail=ERROR_DETAILS["logout_device_required_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not devices.exists():
            raise StandardAPIException(
                code="invalid_input",
                detail=ERROR_DETAILS["invalid_input"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        for device in devices:
            all_token_tuples = list(
                AccessLogManager().get_all_active_tokens_for_device(user_id, device)
            )
            user_manager = HelixUserManager()
            user_manager.logout_tokens(refresh_token_tuples=all_token_tuples)
            device_manager.deactivate_device(device)

        return StandardAPIResponse(status=status.HTTP_200_OK)


class OtpAPIView(generics.GenericAPIView):
    permission_classes = [
        AllowAny,
    ]

    @staticmethod
    def validate_communication_details(request_data):
        email = request_data.get("email", None)
        phone_number = request_data.get("phone_number", None)
        lang = request_data.get("lang", "EN")
        country_code = request_data.get("country_code", DEFAULT_COUNTRY_CODE)
        if not email and not phone_number:
            raise StandardAPIException(
                code="email_phone_missing",
                detail=ERROR_DETAILS["email_phone_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if email:
            try:
                validate_email(value=email)
            except Exception as e:
                logger.info(f"Exception occurred while validating email: {str(e)}")
                raise StandardAPIException(
                    code="invalid_email",
                    detail=ERROR_DETAILS["invalid_email"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        if phone_number and phone_number.startswith("+"):
            raise StandardAPIException(
                code="invalid_phone_number",
                detail=ERROR_DETAILS["invalid_phone_number"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if phone_number and not country_code:
            raise StandardAPIException(
                code="invalid_country_code",
                detail=ERROR_DETAILS["invalid_country_code"].format(
                    country_code=country_code
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return email, phone_number, lang, country_code

    def trigger_forgot_password_otp(self, request_data):
        email, phone_number, lang, country_code = self.validate_communication_details(
            request_data=request_data
        )
        if not HelixUserObjectManager.is_user_with_email_phone_number_exists(
            email, phone_number
        ):
            raise StandardAPIException(
                code="email_does_not_exists",
                detail=ERROR_DETAILS["email_does_not_exists"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        response_user_ids = []
        if email:
            send_otp(
                user=None, type="EMAIL", receiving_address=email, lang=lang, user_type=4
            )
            response_user_ids.append(email)
        if phone_number:
            send_otp(
                user=None,
                type="SMS",
                receiving_address=phone_number,
                lang=lang,
                user_type=4,
                country_code=country_code,
            )
            response_user_ids.append(phone_number)
        return StandardAPIResponse(
            status=status.HTTP_201_CREATED,
            data={
                "user_ids": response_user_ids,
                "user_type": 4,
                "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
        )

    @staticmethod
    def verify_forgot_password_otp(request, request_data):
        user_ids = request_data.get("user_ids")
        code = request_data.get("code")
        if user_ids is None or code is None:
            raise StandardAPIException(
                code="user_id_or_code_missing",
                detail=ERROR_DETAILS["user_id_or_code_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        staff_or_resident = Resident.objects.filter(
            Q(user__email__in=user_ids) | Q(user__phone__in=user_ids)
        ).first()
        if not staff_or_resident:
            staff_or_resident = HelixStaff.objects.filter(
                Q(user__email__in=user_ids) | Q(user__phone__in=user_ids)
            ).first()
        if not staff_or_resident:
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        user_obj = staff_or_resident.user
        if not VerificationCodeManager.is_code_valid(
            user_ids=user_ids, code=code, user_type=4
        ):
            raise StandardAPIException(
                code="invalid_otp",
                detail=ERROR_DETAILS["invalid_otp"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        reset_password_token_expiry = int(time.time()) + RESET_PASSWORD_TOKEN_EXPIRY
        common_token_identity = {
            "tenant": request.tenant,
            "expiry": reset_password_token_expiry,
            "sub_token_type": "reset_password",
        }
        reset_password_token = (
            str(
                HelixUserAccessToken.for_reset_password(
                    user=user_obj, **common_token_identity
                )
            )
            if user_obj.is_staff
            else str(
                ResidentAccessToken.for_tenant_resident(
                    resident=staff_or_resident, **common_token_identity
                )
            )
        )
        response_data = {
            "user_ids": user_ids,
            "user_type": 4,
            "reset_password_token": reset_password_token,
            "staff": user_obj.is_staff,
        }
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    # def trigger_guest_login_otp(self, request_data):
    #     email, phone_number, lang, country_code = self.validate_communication_details(
    #         request_data=request_data
    #     )

    #     dob = request_data.get("dob")
    #     zipcode = request_data.get("zipcode")
    #     if ResidentManager.get_full_resident(
    #         email=email, phone_number=phone_number, dob=dob, zipcode=zipcode
    #     ):
    #         raise StandardAPIException(
    #             code="guest_patient_does_not_exist",
    #             detail=ERROR_DETAILS["guest_patient_does_not_exist"],
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )

    #     response_user_ids = []
    #     if email:
    #         send_otp(
    #             user=None, type="EMAIL", receiving_address=email, lang=lang, user_type=5
    #         )
    #         response_user_ids.append(email)
    #     if phone_number:
    #         send_otp(
    #             user=None,
    #             type="SMS",
    #             receiving_address=phone_number,
    #             lang=lang,
    #             user_type=5,
    #             country_code=country_code,
    #         )
    #         response_user_ids.append(phone_number)
    #     return StandardAPIResponse(
    #         status=status.HTTP_201_CREATED,
    #         data={
    #             "user_ids": response_user_ids,
    #             "user_type": 5,
    #             "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
    #         },
    #     )

    # def trigger_patient_create_otp(self, request_data):
    #     email, phone_number, lang, country_code = self.validate_communication_details(
    #         request_data=request_data
    #     )
    #     if ResidentManager.is_resident_with_email_phone_number_exists(
    #         email, phone_number
    #     ):
    #         raise StandardAPIException(
    #             code="patient_exists",
    #             detail=ERROR_DETAILS["patient_exists"],
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )
    #     response_user_ids = []
    #     if email:
    #         send_otp(
    #             user=None,
    #             type="EMAIL",
    #             receiving_address=email,
    #             lang=lang,
    #             country_code=country_code,
    #         )
    #         response_user_ids.append(email)
    #     if phone_number:
    #         send_otp(
    #             user=None,
    #             type="SMS",
    #             receiving_address=phone_number,
    #             lang=lang,
    #             country_code=country_code,
    #         )
    #         response_user_ids.append(phone_number)
    #     return StandardAPIResponse(
    #         status=status.HTTP_201_CREATED,
    #         data={
    #             "user_ids": response_user_ids,
    #             "user_type": 3,
    #             "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
    #         },
    #     )

    # def trigger_customer_onboarding_otp(self, request_data):
    #     email, _, lang, country_code = self.validate_communication_details(
    #         request_data=request_data
    #     )
    #     email = request_data.get("email")
    #     provider = HelixStaff.objects.filter(user__email__iexact=email).first()

    #     if provider:
    #         if provider.user.is_active:
    #             raise StandardAPIException(
    #                 code="user_already_verified",
    #                 detail=ERROR_DETAILS["user_already_verified"],
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #             )

    #         raise StandardAPIException(
    #             code="inactive_user_exists",
    #             detail=ERROR_DETAILS["inactive_user_exists"],
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )

    #     send_otp(
    #         user=None,
    #         type="EMAIL",
    #         receiving_address=email,
    #         lang=lang,
    #         country_code=country_code,
    #         user_type=5,
    #     )

    #     return StandardAPIResponse(
    #         status=status.HTTP_201_CREATED,
    #         data={
    #             "user_ids": [email],
    #             "user_type": 5,
    #             "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
    #         },
    #     )

    # def verify_customer_onboarding_otp(self, request_data, tenant):
    #     email = request_data.get("email")
    #     code = request_data.get("code")
    #     if not email or not code:
    #         raise StandardAPIException(
    #             code="email_or_code_missing",
    #             detail=ERROR_DETAILS["email_or_code_missing"],
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )

    #     if not VerificationCodeManager.is_code_valid(
    #         user_ids=[email], code=code, user_type=5
    #     ):
    #         raise StandardAPIException(
    #             code="invalid_otp",
    #             detail=ERROR_DETAILS["invalid_otp"],
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #         )

    #     customer_onboarding_exp = int(time.time()) + CUSTOMER_ONBOARDING_TOKEN_EXPIRY
    #     token = HelixUserAccessToken.for_customer_onboarding(
    #         tenant=tenant,
    #         user={"email": email},
    #         expiry=customer_onboarding_exp,
    #         sub_token_type="customer_onboarding",
    #     )
    #     response_data = {
    #         "user_ids": [email],
    #         "user_type": 5,
    #         "customer_onboarding_token": str(token),
    #     }
    #     return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    def trigger_rental_application_view_otp(self, request_data):
        email, _, lang, country_code = self.validate_communication_details(
            request_data=request_data
        )
        email = request_data.get("email")
        user = Resident.objects.filter(user__email__iexact=email).first()
        if not user:
            raise StandardAPIException(
                code="invalid_email",
                detail=ERROR_DETAILS["invalid_email"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        send_otp(
            user=user,
            type="EMAIL",
            receiving_address=email,
            lang=lang,
            country_code=country_code,
            user_type=5,
        )

        return StandardAPIResponse(
            status=status.HTTP_201_CREATED,
            data={
                "user_ids": [user.id],
                "user_type": 5,
                "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
        )

    def rental_application(self, user_id):
        return (
            Application.objects.filter(
                resident=user_id,
                status=LeaseApplicationStatus.SENT.value,
            )
            .order_by("-updated_on")
            .first()
        )

    def verify_rental_application_view_otp(self, request_data, tenant):
        user_id = request_data.get("user_id")
        code = request_data.get("code")
        if user_id is None or code is None:
            raise StandardAPIException(
                code="user_id_or_code_missing",
                detail=ERROR_DETAILS["user_id_or_code_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not VerificationCodeManager.is_code_valid(
            user_ids=[user_id], code=code, user_type=5
        ):
            raise StandardAPIException(
                code="invalid_otp",
                detail=ERROR_DETAILS["invalid_otp"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        resident = Resident.objects.get(id=user_id)
        rental_application_view_exp = int(time.time()) + OTP_EXPIRY_IN_SECONDS
        token = HelixUserAccessToken.for_rental_application_view(
            tenant=tenant,
            user=resident,
            expiry=rental_application_view_exp,
            sub_token_type="rental_application_view",
        )
        application = self.rental_application(user_id)
        unit_id = None
        application_id = None

        if application and application.unit:
            unit_id = application.unit.id
            application_id = application.id
        response_data = {
            "user_id": user_id,
            "user_type": 5,
            "unit_id": unit_id,
            "application_id": application_id,
            "rental_application_view_token": str(token),
        }
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        action = request.data.get("action", "send").lower()
        otp_type = request.data.get("otp_type", "").lower()

        # if action == "send" and otp_type == "patient_create":
        #     return self.trigger_patient_create_otp(request_data=request.data)

        if action == "resend":
            user_ids = request.data.get("user_ids")
            user_type = request.data.get("user_type")
            channel = request.data.get("channel", "EMAIL")
            if not user_ids or not user_type:
                raise StandardAPIException(
                    code="user_id_type_missing",
                    detail=ERROR_DETAILS["user_id_type_missing"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            user_id = user_ids[0]
            if not is_valid_uuid(user_id):
                raise StandardAPIException(
                    code="invalid_user_id",
                    detail=ERROR_DETAILS["invalid_user_id"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            success, error_code = VerificationCodeManager().resend_code(
                user_id, user_type, channel
            )
            if not success:
                raise StandardAPIException(
                    code=error_code,
                    detail=ERROR_DETAILS[error_code],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            return StandardAPIResponse(
                status=status.HTTP_201_CREATED,
                data={
                    "user_id": user_id,
                    "user_type": user_type,
                    "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
                },
            )

        # if otp_type == "guest_login" and action == "send":
        #     return self.trigger_guest_login_otp(request_data=request.data)

        if otp_type == "forgot_password" and action == "send":
            return self.trigger_forgot_password_otp(request_data=request.data)

        if otp_type == "forgot_password" and action == "verify":
            return self.verify_forgot_password_otp(
                request=request, request_data=request.data
            )

        if otp_type == "reset_password":
            email = request.data.get("email", None)
            lang = request.data.get("lang", "EN")
            if not email:
                raise StandardAPIException(
                    code="email_missing",
                    detail=ERROR_DETAILS["email_missing"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            user = get_user(email)
            if not user:
                return Response(
                    {"message": "Details provided is incorrect"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            parent_obj = get_resident_or_staff_by_user(user)
            if not parent_obj:
                raise StandardAPIException(
                    code="invalid_user_id",
                    detail=ERROR_DETAILS["invalid_user_id"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            send_otp(parent_obj, "EMAIL", None, lang)
            # Generate Event
            return Response(
                {"message": "Password reset request has been registerd"},
                status=status.HTTP_201_CREATED,
            )

        # if action == "send" and otp_type == "customer_onboarding":
        #     return self.trigger_customer_onboarding_otp(request_data=request.data)

        # if action == "verify" and otp_type == "customer_onboarding":
        #     return self.verify_customer_onboarding_otp(
        #         request_data=request.data, tenant=request.tenant
        #     )
        if action == "send" and otp_type == "rental_application_view":
            return self.trigger_rental_application_view_otp(request_data=request.data)

        if action == "verify" and otp_type == "rental_application_view":
            return self.verify_rental_application_view_otp(
                request_data=request.data, tenant=request.tenant
            )

        raise StandardAPIException(
            code="invalid_action",
            detail=ERROR_DETAILS["invalid_action"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class UserUnlockAPIView(APIView):
    permission_classes = [HelixUserBasePermission]
    entity = "HelixStaff"

    def post(self, request):
        user_ids = request.data.get("user_ids", [])

        if not isinstance(user_ids, list) or not any(
            is_valid_uuid(uid) for uid in user_ids
        ):
            raise StandardAPIException(
                code="invalid_list_of_user_ids",
                detail=ERROR_DETAILS["invalid_list_of_user_ids"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        users = HelixUser.objects.filter(id__in=user_ids)
        updated_count = users.update(locked=False, failed_attempt_count=0)

        ##TODO: need to handle for residousers seperatly
        sent_to = []
        for user in users:
            if user.is_staff:
                NotificationQueueManager.send_email_notification(
                    user.helixuser_staff,
                    TemplateCode.ACCOUNT_UNLOCK_NOTIFICATION.value,
                )
                sent_to.append(user.id)

        response = {
            "message": ERROR_DETAILS["unlocked_message"].format(
                updated_count=updated_count
            ),
            "updated_ids": sent_to,
            "not_updated_ids": [
                user.id for user in users if str(user.id) not in user_ids
            ],
        }

        return StandardAPIResponse(
            data=response,
            status=status.HTTP_200_OK,
        )


class UserRoleModulePermissionView(APIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    # no entity definition required as this api should be accessible by every HelixStaff user

    def get(self, request, *args, **kwargs):
        user = request.user
        roles = user.helixuser_staff.user_roles.filter(is_role_active=True)
        module_perms = ModulePermission.objects.filter(role__in=roles).select_related(
            "module"
        )
        obj = {}
        for perm in module_perms:
            if obj.get(perm.module.id):
                old_perm = obj.get(perm.module.id)
                if perm.can_view:
                    old_perm.can_view = perm.can_view
                if perm.can_update:
                    old_perm.can_update = perm.can_update
                if perm.can_delete:
                    old_perm.can_delete = perm.can_delete
                if perm.can_create:
                    old_perm.can_create = perm.can_create
            else:
                obj[perm.module.id] = perm
        data = ModulePermissionReadOnlySerializer(list(obj.values()), many=True).data
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class UserRoleSubModulePermissionView(APIView):
    permission_classes = [HelixUserBasePermission]
    # no entity definition required as this api should be accessible by every HelixStaff user

    def get(self, request, *args, **kwargs):
        user = request.user
        module_id = kwargs.get("module_id")
        roles = user.helixuser_staff.user_roles.filter(is_role_active=True)
        perms = SubModulePermission.objects.filter(
            role__in=roles, submodule__module_id=module_id
        ).select_related("submodule")
        obj = {}
        for perm in perms:
            if obj.get(perm.submodule.id):
                old_perm = obj.get(perm.submodule.id)
                if perm.can_view:
                    old_perm.can_view = perm.can_view
                if perm.can_update:
                    old_perm.can_update = perm.can_update
                if perm.can_delete:
                    old_perm.can_delete = perm.can_delete
                if perm.can_create:
                    old_perm.can_create = perm.can_create
            else:
                obj[perm.submodule.id] = perm
        data = SubmodulePermissionReadOnlySerializer(list(obj.values()), many=True).data
        return StandardAPIResponse(data=data, status=status.HTTP_200_OK)


class CareCenterRole(StandardListAPIMixin):
    permission_classes = [AllowAny]
    serializer_class = CareCenterRoleSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)

    def get_queryset(self):
        return [
            {"code": code, "display_name": display}
            for code, display in CareCenterRoleType.choices()
        ]


class UserRoleCountView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission]
    entity = "UserRole"

    def get(self, request, *args, **kwargs):
        role_count = UserRole.objects.all().count()
        role_group_count = UserGroup.objects.all().count()
        data = {
            "role_count": role_count,
            "role_group_count": role_group_count,
        }
        return StandardAPIResponse(data, status=status.HTTP_200_OK)


class UserResetPasswordAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedHelixUser]
    authentication_classes = [UserResetPasswordAuthentication]

    allowed_methods_to_resident = {
        **ALLOWED_METHODS_TO_PATIENT,
        "post": True,
    }

    @staticmethod
    def post(request, *args, **kwargs):
        user_obj = request.user
        new_password = request.data.get("password")
        if not new_password:
            raise StandardAPIException(
                code="invalid_password",
                detail=ERROR_DETAILS["invalid_password"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if user_obj.check_password(new_password):
            raise StandardAPIException(
                code="duplicate_password",
                detail=ERROR_DETAILS["duplicate_password"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user_manager = HelixUserManager(user_obj=user_obj, email=user_obj.email)
        user_manager.change_password(password=new_password, approve_if_pending=True)

        update_device_access(
            user=user_obj,
            refresh=None,
            device_detail=request.data.get("device_detail", None),
            location_detail=request.data.get("location_detail", {}),
        )

        # Send pending application emails after successful password setup
        send_pending_application_emails(user_obj)

        final_response_data = {"password_reset": True}
        return StandardAPIResponse(data=final_response_data, status=status.HTTP_200_OK)


class PolicyListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    queryset = Policy.objects.all().prefetch_related("versions")
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    pagination_class = StandardPageNumberPagination
    search_fields = ["name", "policy_type"]
    filterset_fields = ["policy_type", "status", "publishing_date"]
    entity = "Policy"

    def get_serializer_class(self):
        # Use PolicyListSerializer for list view, PolicyDetailSerializer for detail
        if self.request.method in ["POST"]:
            return PolicyDetailSerializer
        return PolicyListSerializer


class PoliciesCountAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    queryset = Policy.objects.all()

    def get(self, request):
        policy_counts = {}

        from lookup.models import Lookup

        statuses = Lookup.objects.filter(name="POLICY_STATUS", active=True).values_list(
            "code", flat=True
        )

        for status_code in statuses:
            count = Policy.objects.filter(status=status_code).count()
            policy_counts[status_code] = count

        return StandardAPIResponse(data=policy_counts, status=status.HTTP_200_OK)


class PolicyGetUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    queryset = Policy.objects.all().prefetch_related("versions")
    serializer_class = PolicyDetailSerializer
    entity = "Policy"

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if "status" in request.data and len(request.data) == 1:
            instance.status = request.data["status"]
            instance.save()
            serializer = self.get_serializer(instance)
            return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)

        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class UserAcceptanceFilter(django_filters.FilterSet):
    patient = django_filters.CharFilter(
        field_name="user__resident__id", lookup_expr="exact"
    )

    class Meta:
        model = UserPolicyAcceptance
        fields = (
            "patient",
            "policy_version",
        )


class UserAcceptanceListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True, "post": True}
    queryset = UserPolicyAcceptance.objects.for_current_user()
    serializer_class = UserPolicyAcceptanceSerializer
    entity = "UserPolicyAcceptance"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = [
        "policy_version__policy__name",
    ]
    filterset_class = UserAcceptanceFilter

    def list(self, request, *args, **kwargs):
        policies = request.query_params.get("policies")
        renter_id = request.query_params.get("renter_id")
        user = request.user
        if not policies:
            raise StandardAPIException(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(param="policies"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        policy_ids = policies.split(",")
        if request.user.is_staff and renter_id:
            pat_obj = Resident.objects.filter(id=renter_id).first()
            if not pat_obj or not pat_obj.user:
                raise StandardAPIException(
                    code="invalid_renter_id",
                    detail=ERROR_DETAILS["invalid_renter_id"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            user = pat_obj.user

        # obtained user accepted policy's all versions
        user_accepted_policies_version = UserPolicyAcceptance.objects.filter(
            user=user, policy_version__policy_id__in=policy_ids
        ).select_related("policy_version")

        # aggregated to the latest version accepted of each policy
        policy_versions_accepted_by_user = {}
        for i in user_accepted_policies_version:
            if (
                policy_versions_accepted_by_user.get(str(i.policy_version.policy_id), 0)
                < i.policy_version.version_number
            ):
                policy_versions_accepted_by_user[
                    str(i.policy_version.policy_id)
                ] = i.policy_version.version_number

        # obtained latest version available now of all policies
        policies_latest_version = (
            PolicyVersion.objects.filter(policy_id__in=policy_ids)
            .values("policy_id")
            .annotate(latest_version=Max("version_number"))
        )

        # compared whether user has accepted latest version or not
        response = []
        for obj in policies_latest_version:
            accepted = False
            if (
                policy_versions_accepted_by_user.get(str(obj["policy_id"]), 0)
                >= obj["latest_version"]
            ):
                accepted = True
            response.append(
                {"policy_id": obj["policy_id"], "latest_version_accepted": accepted}
            )
        return StandardAPIResponse(data=response, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        user = request.user
        if user.is_staff and request.data.get("renter_id"):
            renter_id = request.data.get("renter_id")
            pat_obj = Resident.objects.filter(id=renter_id).first()
            if not pat_obj or not pat_obj.user:
                raise StandardAPIException(
                    code="invalid_renter_id",
                    detail=ERROR_DETAILS["invalid_renter_id"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            user = pat_obj.user
        policy = request.data.get("policy", None)
        if not policy:
            raise StandardAPIException(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(param="policy"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        policy = Policy.objects.filter(id=policy).first()
        if not policy:
            raise StandardAPIException(
                code="invalid_id",
                detail=ERROR_DETAILS["invalid_id"].format(param="policy"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        version = policy.versions.all().order_by("-version_number").first()
        if not version:
            raise StandardAPIException(
                code="invalid_id",
                detail=ERROR_DETAILS["invalid_id"].format(param="policy"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        create_data = {"user": user.id, "policy_version_id": version.id}
        serializer = self.get_serializer(data=create_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ActivateUsers(APIView):
    permission_classes = [HelixUserBasePermission]
    entity = "HelixStaff"

    def post(self, request):
        user_ids = request.data.get("user_ids", [])
        active_value = request.data.get("active")
        active = active_value is True or active_value == "true"

        if user_ids is None or not any(is_valid_uuid(uid) for uid in user_ids):
            raise StandardAPIException(
                code="invalid_user_id",
                detail=ERROR_DETAILS["invalid_user_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        users = get_users(user_ids)

        if not users.exists():
            raise StandardAPIException(
                code="user_ids_not_found",
                detail=ERROR_DETAILS["user_ids_not_found"],
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        updated_count = users.update(
            is_active=active, status="APPROVED" if active else "INACTIVE"
        )

        # When deactivating users (marking as INACTIVE), also update their leases to EXPIRED
        if not active:
            Lease.objects.filter(resident__user__in=users).update(
                status=LeaseStatus.EXPIRED.value
            )

        sent_to = []
        for user in users:
            if user.is_staff:
                NotificationQueueManager.send_email_notification(
                    user.helixuser_staff,
                    TemplateCode.ACCOUNT_ACTIVATE_NOTIFICATION.value,
                )
                sent_to.append(user.id)

        return StandardAPIResponse(
            {
                "message": ERROR_DETAILS["activate_deactivate_message"].format(
                    action="activated" if active else "de-activated",
                    updated_count=updated_count,
                ),
                "not_updated_user_ids": [
                    user.id for user in users if str(user.id) not in user_ids
                ],
                "updated_user_ids": sent_to,
            },
            status=status.HTTP_200_OK,
        )
