import django_filters

from django.contrib.contenttypes.models import ContentType
from django.db.models import Max, Q
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.helix_pagination import StandardPageNumberPagination
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardUpdateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
)
from common.response import StandardAPIResponse
from common.permissions import HelixUserBasePermission
from helixauth.serializers import HelixUserReceipientSerialiser
from patients.serializers import PatientRecipientSerialiser

from .models import (
    DELIVERY_STATUS_CHOICES,
    SMS,
    Email,
    EmailRecipient,
    SMSRecipient,
    EmailTemplate,
)
from .serializers import (
    CreateEmailSerializer,
    CreateSMSSerializer,
    ListEmailSerializer,
    ListSMSSerializer,
    MarkAsReadSerializer,
    SMSInboxSerializer,
    UpdateDraftEmailSerializer,
    EmailTemplateSerializer,
)


# Define the Email Filter for status
class EmailFilter(filters.FilterSet):
    is_draft = filters.BooleanFilter(field_name="is_draft")
    is_archive = filters.BooleanFilter(field_name="is_archive")
    status = filters.ChoiceFilter(
        field_name="status",
        choices=DELIVERY_STATUS_CHOICES,
        help_text="Filter by status",
    )

    class Meta:
        model = Email
        fields = ["delivery_status", "is_draft", "is_archive"]


# Define the view combining POST and GET (List) APIs for Email
class CreateListEmailAPIView(StandardListCreateAPIMixin):
    queryset = Email.objects.filter(
        parent_email__isnull=True
    )  # Always return root level emails
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = EmailFilter
    pagination_class = StandardPageNumberPagination
    filter_fields = ("delivery_status", "is_draft", "is_archive")
    search_fields = ("subject", "email_recipients__email_address")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateEmailSerializer
        return ListEmailSerializer

    def get_serializer_context(self):
        # Add related object serializers to the context
        context = super().get_serializer_context()
        context.update(
            {
                "helixuser_serializer": HelixUserReceipientSerialiser,
                "patient_serializer": PatientRecipientSerialiser,
            }
        )
        return context

    def perform_create(self, serializer):
        # Automatically set the `created_by` to the authenticated user
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """
        Filter emails based on the current user and optional 'inbox' query parameter.
        """
        queryset = super().get_queryset()

        # Check if 'inbox' and body_search query parameter is present
        inbox = self.request.query_params.get("inbox", None)

        if inbox is not None:
            # Filter emails where the user is a recipient (in the inbox)
            queryset = queryset.filter(
                email_recipients__email_address=self.request.user.email
            ).distinct()
        else:
            # Default: Return emails created by the user
            queryset = queryset.filter(created_by=self.request.user)
        body_search = self.request.query_params.get("body_search", None)

        if body_search:
            # Filter emails by searching in the body
            queryset = queryset.filter(body__icontains=body_search)

        return queryset.order_by("-created_on", "-sent_at")

    def post(self, request, *args, **kwargs):
        # Handle the POST request for creating an email
        payload = request.data
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return StandardAPIResponse(
            data=serializer.data,
            headers=headers,
            status=status.HTTP_201_CREATED,
        )


class UpdateDraftToSentAPIView(StandardUpdateAPIMixin):
    serializer_class = UpdateDraftEmailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter drafts created by the authenticated user only
        return Email.objects.for_current_user()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)
        queryset = queryset.filter(is_draft=True, created_by=self.request.user)

        if self.request.data["is_archive"]:
            return Email.objects.filter(
                Q(created_by=self.request.user, is_archive=True)
                | Q(email_recipients__email_address=self.request.user, is_archive=True)
            )

        return queryset


class MarkEmailAsReadAPIView(generics.UpdateAPIView):
    """
    API to mark emails as read for the logged-in user using email_id (UUID).
    """

    queryset = EmailRecipient.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = MarkAsReadSerializer
    lookup_field = "email_id"

    def get_queryset(self):
        email_id = self.kwargs.get("email_id")
        return EmailRecipient.objects.filter(
            email__id=email_id,  # Filter by email_id (UUID)
            email_address=self.request.user.email,  # Ensure the recipient belongs to the logged-in user
            read_status=False,  # Only include unread emails
        )

    def perform_update(self, serializer):
        # Automatically set read_status to True and read_at to the current time
        serializer.save(read_status=True, read_at=timezone.now())


class CreateListSMSAPIView(StandardListCreateAPIMixin):
    queryset = SMS.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    pagination_class = StandardPageNumberPagination
    filter_fields = ["delivery_status"]
    search_fields = ["body"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateSMSSerializer
        return ListSMSSerializer

    def get_serializer_context(self):
        # Add related object serializers to the context
        context = super().get_serializer_context()
        context.update(
            {
                "helixuser_serializer": HelixUserReceipientSerialiser,
                "patient_serializer": PatientRecipientSerialiser,
            }
        )
        return context

    def perform_create(self, serializer):
        # Automatically set the `created_by` to the authenticated user
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        """
        Filter emails based on the current user and optional 'inbox' query parameter.
        """
        queryset = super().get_queryset()
        # Get the logged-in user
        user = self.request.user

        # Retrieve the recipient ID from query parameters
        recipient_id = self.request.query_params.get("recipient_id", None)

        if recipient_id:
            # Apply the filtering logic
            queryset = queryset.filter(
                Q(created_by=recipient_id, sms_recipients__object_id=user.id)
                | Q(created_by=user.id, sms_recipients__object_id=recipient_id)
            ).distinct()
        else:
            # Default: Return emails created by the user
            queryset = queryset.filter(created_by=self.request.user)
        return queryset.order_by("-created_on", "-sent_at")

    def post(self, request, *args, **kwargs):
        # Handle the POST request for creating an email
        payload = request.data
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return StandardAPIResponse(
            data=serializer.data,
            headers=headers,
            status=status.HTTP_201_CREATED,
        )


class SMSInboxView(StandardListCreateAPIMixin):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    serializer_class = SMSInboxSerializer
    search_fields = ["sms__body", "phone"]

    def get_queryset(self):
        # Get the logged-in user
        user = self.request.user

        # Query for recipients
        queryset = SMSRecipient.objects.filter(
            Q(created_by=user),
            object_id__isnull=False,
            content_type__isnull=False,
        ).exclude(object_id=user.id)

        return queryset

    def filter_queryset(self, queryset):
        # Apply the content type filter if specified
        # Define a mapping for the content type filters
        content_type_mapping = {
            "STAFF": "helixuser",
            "PATIENT": "patient",
        }
        # Get the `other_participants_type` query parameter
        other_participants_type = self.request.query_params.get(
            "other_participants_type", None
        )
        model_name = content_type_mapping.get(other_participants_type)
        # Apply the content type filter if the parameter matches
        content_type = ContentType.objects.filter(model=model_name).first()
        if content_type:
            content_type_id = content_type.id
            queryset = queryset.filter(content_type=content_type_id)

        # Annotate and order the queryset
        queryset = (
            queryset.values("object_id", "content_type")
            .annotate(latest_sent_at=Max("sms__sent_at"))
            .order_by("-latest_sent_at")
        )

        return super().filter_queryset(queryset)

    def get_serializer_context(self):
        # Add related object serializers to the context
        context = super().get_serializer_context()
        context.update(
            {
                "helixuser_serializer": HelixUserReceipientSerialiser,
                "patient_serializer": PatientRecipientSerialiser,
            }
        )
        return context


class BulkMarkEmailAsReadAPIView(APIView):
    """
    API to mark multiple emails as read/unread for the logged-in user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Retrieve email IDs and read status from the request body
        email_ids = request.data.get("email_ids", [])
        read_status = request.data.get(
            "read_status", True
        )  # Default to marking as read
        if not email_ids or not isinstance(email_ids, list):
            return StandardAPIResponse(
                data={"error": "email_ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Filter EmailRecipient objects for the logged-in user
        recipients = EmailRecipient.objects.filter(
            email__id__in=email_ids,  # Filter by the provided email IDs
            email_address=request.user.email,  # Ensure the recipient belongs to the logged-in user
        )

        if not recipients.exists():
            return StandardAPIResponse(
                data={"error": "No matching emails found for the current user."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Update read_status and read_at
        now = timezone.now()
        recipients.update(read_status=read_status, read_at=now if read_status else None)

        return StandardAPIResponse(
            data={
                "message": f"Emails successfully marked as {'read' if read_status else 'unread'}."
            },
            status=status.HTTP_200_OK,
        )


class EmailTemplateFilter(django_filters.FilterSet):
    provider = django_filters.CharFilter(field_name="provider__id", lookup_expr="exact")
    is_active = django_filters.CharFilter(
        field_name="is_active", lookup_expr="icontains"
    )
    provider_email = django_filters.CharFilter(
        field_name="provider__user__email", lookup_expr="icontains"
    )
    provider_first_name = django_filters.CharFilter(
        field_name="provider__user__first_name", lookup_expr="icontains"
    )
    provider_last_name = django_filters.CharFilter(
        field_name="provider__user__last_name", lookup_expr="icontains"
    )
    provider_username = django_filters.CharFilter(
        field_name="provider__user__username", lookup_expr="icontains"
    )

    class Meta:
        model = EmailTemplate
        fields = (
            "provider",
            "is_active",
            "provider_email",
            "provider_first_name",
            "provider_last_name",
            "provider_username",
        )


class EmailTemplateCreateListAPIView(StandardListCreateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    queryset = EmailTemplate.objects.for_current_user()
    serializer_class = EmailTemplateSerializer
    filter_backends = [filters.DjangoFilterBackend, SearchFilter]
    filterset_class = EmailTemplateFilter
    pagination_class = StandardPageNumberPagination
    search_fields = ["template_name"]
    entity = "EmailTemplate"


class EmailTemplateRetrieveUpdateDestroyAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    queryset = EmailTemplate.objects.for_current_user()
    serializer_class = EmailTemplateSerializer
    entity = "EmailTemplate"
