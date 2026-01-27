from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated

from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.helix_pagination import StandardPageNumberPagination
from common.mixins import StandardListCreateAPIMixin, StandardRetrieveUpdateAPIMixin
from common.response import StandardAPIResponse
from common.utils.parser import WebhookJSONParser
from helixauth.authentication.kc import KeyCloakAuthentication
from helixauth.managers.user.generic import HelixUserManager
from meetings.constants import (
    SessionListMode,
    MeetingSessionType,
    NotificationType,
    OtherParticipantType,
)
from meetings.filters import MeetingMessageFilter, MeetingFilter
from meetings.managers.meeting import MeetingManager
from meetings.models import Meeting, MeetingParticipant, MeetingSession, MeetingMessage
from meetings.processor.event import MeetingEventProcessor
from meetings.serializers.meeting import MeetingSerializer
from meetings.serializers.message import MeetingMessageSerializer
from meetings.serializers.participant import MeetingParticipantSerializer
from meetings.serializers.session import MeetingSessionSerializer


class MeetingsListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = MeetingFilter
    ordering = (
        # "-meetingsession__meetingmessage__created_on",
        "-created_on",
    )
    permission_classes = [IsAuthenticated]
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer

    @staticmethod
    def filter_by_other_participant_type(queryset, other_participants_type):
        patients_in_participation = False
        if other_participants_type in [
            OtherParticipantType.PATIENT.value,
            OtherParticipantType.STAFF_AND_PATIENTS.value,
        ]:
            patients_in_participation = True

        return queryset.filter(patients_in_participation=patients_in_participation)

    @staticmethod
    def filter_by_participant_name(queryset, participant_name):
        return queryset.filter(
            Q(meetingparticipant__staff__user__first_name__icontains=participant_name)
            | Q(meetingparticipant__staff__user__last_name__icontains=participant_name)
            | Q(meetingparticipant__patient__first_name__icontains=participant_name)
            | Q(meetingparticipant__patient__last_name__icontains=participant_name)
        )

    @staticmethod
    def filter_by_staff_name(queryset, staff_name):
        return queryset.filter(
            Q(meetingparticipant__staff__user__first_name__icontains=staff_name)
            | Q(meetingparticipant__staff__user__last_name__icontains=staff_name)
        )

    @staticmethod
    def filter_by_patient_name(queryset, patient_name):
        return queryset.filter(
            Q(meetingparticipant__patient__first_name__icontains=patient_name)
            | Q(meetingparticipant__patient__last_name__icontains=patient_name)
        )

    def apply_custom_filters(self, queryset):
        other_participants_type = self.request.query_params.get(
            "other_participants_type"
        )
        participant_name = self.request.query_params.get("participant_name")
        staff_name = self.request.query_params.get("staff_name")
        patient_name = self.request.query_params.get("patient_name")
        if other_participants_type:
            queryset = self.filter_by_other_participant_type(
                queryset=queryset, other_participants_type=other_participants_type
            )
        if participant_name:
            queryset = self.filter_by_participant_name(
                queryset=queryset, participant_name=participant_name
            )
        if staff_name:
            queryset = self.filter_by_staff_name(
                queryset=queryset, staff_name=staff_name
            )
        if patient_name:
            queryset = self.filter_by_patient_name(
                queryset=queryset, patient_name=patient_name
            )

        return queryset

    def filter_queryset(self, queryset):
        queryset = super(MeetingsListCreateAPIView, self).filter_queryset(queryset)
        return self.apply_custom_filters(queryset=queryset)


class MeetingsRetrieveUpdateAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [IsAuthenticated]
    queryset = Meeting.objects.all()
    serializer_class = MeetingSerializer


class MeetingParticipantMixin:
    @classmethod
    def get_validated_meeting_manager(cls, meeting_id):
        meeting_manager = MeetingManager.init(meeting_id=str(meeting_id))
        if not meeting_manager:
            raise StandardAPIException(
                code="meeting_not_found",
                detail=ERROR_DETAILS["meeting_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return meeting_manager

    @classmethod
    def get_validated_participant_manager(cls, meeting_manager, meeting_participant_id):
        participant_manager = meeting_manager.initialize_participant_manager(
            meeting_participant_id=str(meeting_participant_id)
        )
        if not participant_manager:
            raise StandardAPIException(
                code="meeting_participant_not_found",
                detail=ERROR_DETAILS["meeting_participant_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return participant_manager

    @classmethod
    def generate_token(cls, meeting_manager, meeting_participant_id):
        token = meeting_manager.generate_token(
            meeting_participant_id=str(meeting_participant_id)
        )
        if not token:
            raise StandardAPIException(
                code="unknown_error_while_getting_token",
                detail=ERROR_DETAILS["unknown_error_while_getting_token"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return token

    @classmethod
    def get_validated_meeting_participant(cls, meeting_id, staff_id, patient_id):
        meeting_participant = None
        if staff_id and not patient_id:
            meeting_participant = MeetingParticipant.objects.filter(
                Q(meeting_id=str(meeting_id)) & (Q(staff_id=str(staff_id)))
            ).first()
        elif patient_id and not staff_id:
            meeting_participant = MeetingParticipant.objects.filter(
                Q(meeting_id=str(meeting_id)) & (Q(patient_id=str(patient_id)))
            ).first()

        if not meeting_participant:
            raise StandardAPIException(
                code="meeting_participant_not_found",
                detail=ERROR_DETAILS["meeting_participant_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return meeting_participant

    @staticmethod
    def get_validated_participant(meeting_obj, user):
        if user is None:
            return

        user_manager = HelixUserManager(user_obj=user)
        (
            associated_account,
            account_class_name,
        ) = user_manager.get_associated_patient_or_provider()
        if account_class_name == "Patient":
            return meeting_obj.meetingparticipant_set.filter(
                patient_id=str(associated_account.id)
            ).first()

        return meeting_obj.meetingparticipant_set.filter(
            staff_id=str(associated_account.id)
        ).first()


class MeetingParticipantsListCreateAPIView(
    MeetingParticipantMixin, StandardListCreateAPIMixin
):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filter_fields = ("meeting", "id", "staff", "patient", "is_host", "invited")
    ordering = ("-created_on",)
    permission_classes = [AllowAny]
    queryset = MeetingParticipant.objects.all()
    serializer_class = MeetingParticipantSerializer

    def post(self, request, *args, **kwargs):
        meeting_id = self.request.data.get("meeting_id")
        if not meeting_id:
            raise StandardAPIException(
                code="meeting_id_missing",
                detail=ERROR_DETAILS["meeting_id_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        participants_data = request.data.get("participants", [])
        if not participants_data:
            raise StandardAPIException(
                code="participants_data_missing",
                detail=ERROR_DETAILS["participants_data_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        meeting_manager = self.get_validated_meeting_manager(meeting_id=str(meeting_id))
        created_participants = meeting_manager.set_participants(
            participants_data=participants_data
        )
        # TODO send invite only if invite: True is passed
        meeting_manager.send_invites(participants=created_participants)
        participants = self.serializer_class(created_participants, many=True).data

        response_data = {
            "meeting_id": str(meeting_id),
            "link": meeting_manager.meeting_obj.link,
            "participants": participants,
        }

        return StandardAPIResponse(data=response_data, status=status.HTTP_201_CREATED)


class StartMeetingAPIView(GenericAPIView, MeetingParticipantMixin):
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeyCloakAuthentication]
    queryset = Meeting.objects.all()

    @staticmethod
    def generate_token_for_participant(meeting_obj, participant):
        meeting_manager = MeetingManager.init(meeting_id=str(str(meeting_obj.id)))
        return meeting_manager.generate_token(
            meeting_participant_id=str(participant.id)
        )

    def get_started_by(self):
        started_by_patient = getattr(self.request, "is_resident", False)
        started_by = (
            getattr(self.request, "staff", None)
            if not started_by_patient
            else getattr(self.request.user, "patient", None)
        )
        return started_by

    def post(self, request, *args, **kwargs):
        notify = request.data.get("notify", True)
        meeting_obj = self.get_object()
        participant = self.get_validated_participant(
            meeting_obj=meeting_obj,
            user=self.request.user,
        )
        if participant is None:
            raise StandardAPIException(
                code="cannot_start_meeting",
                detail=ERROR_DETAILS["cannot_start_meeting"].format(
                    reason="user_not_a_participant"
                ),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        meeting_manager = MeetingManager(
            meeting_id=str(meeting_obj.id), meeting_obj=meeting_obj
        )
        session_representation = meeting_manager.get_or_create_room_session(
            started_by=participant, notify=notify
        )
        token = self.generate_token_for_participant(
            meeting_obj=meeting_obj, participant=participant
        )
        session_representation["token"] = token
        session_representation["current_participant"] = str(participant.id)
        session_representation["current_participant_name"] = str(participant.name)
        session_representation["current_participant_is_staff"] = participant.is_staff
        return StandardAPIResponse(
            data=session_representation, status=status.HTTP_201_CREATED
        )


class MeetingSessionsListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filter_fields = ("meeting", "id", "session_id", "active")
    ordering = ("-created_on",)
    permission_classes = [AllowAny]
    queryset = MeetingSession.objects.all()
    serializer_class = MeetingSessionSerializer
    pagination_class = StandardPageNumberPagination

    def filter_queryset(self, queryset):
        qs = super(MeetingSessionsListCreateAPIView, self).filter_queryset(
            queryset=queryset
        )

        if self.request.query_params.get("staff"):
            staff_id = self.request.query_params.get("staff")
            qs = qs.filter(meeting__meetingparticipant__staff_id=staff_id)

        if self.request.query_params.get("patient"):
            patient_id = self.request.query_params.get("patient")
            qs = qs.filter(meeting__meetingparticipant__patient_id=patient_id)

        return qs

    @staticmethod
    def _append_additional_session_properties(paginated_response_data, context):
        if not context:
            return paginated_response_data

        for session in paginated_response_data:
            session["_type"] = (
                MeetingSessionType.INCOMING.value
                if session["created_by"] != context
                else MeetingSessionType.OUTGOING.value
            )

        return paginated_response_data

    def append_additional_session_properties(self, paginated_response_data):
        mode = self.request.query_params.get("mode", SessionListMode.LIST.value)
        if mode == SessionListMode.LIST.value:
            return paginated_response_data

        staff_id = self.request.query_params.get("staff")
        patient_id = self.request.query_params.get("patient")
        if not staff_id and not patient_id:
            return paginated_response_data

        context = None
        if staff_id and not patient_id:
            context = staff_id

        if patient_id and not staff_id:
            context = patient_id

        if patient_id and staff_id:
            context = self.request.query_params.get("context", staff_id)
            if context != staff_id and context != patient_id:
                return paginated_response_data

        return self._append_additional_session_properties(
            paginated_response_data=paginated_response_data,
            context=context,
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = (
            self.get_serializer(page, many=True) if page is not None else queryset
        )
        paginated_response_data = serializer.data
        paginated_response_data = self.append_additional_session_properties(
            paginated_response_data=paginated_response_data
        )
        if page is not None:
            return self.get_paginated_response(paginated_response_data)

        return StandardAPIResponse(paginated_response_data)


class MeetingTokenAPIView(MeetingParticipantMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeyCloakAuthentication]

    def post(self, request, *args, **kwargs):
        meeting_id = kwargs.pop("meeting_id")
        participant_id = kwargs.pop("participant_id")

        meeting_manager = self.get_validated_meeting_manager(meeting_id=meeting_id)
        meeting_obj = meeting_manager.meeting_obj
        participant = self.get_validated_participant(
            meeting_obj=meeting_obj,
            user=self.request.user,
        )
        if participant is None:
            raise StandardAPIException(
                code="cannot_generate_token",
                detail=ERROR_DETAILS["cannot_generate_token"].format(
                    reason="user_not_a_participant"
                ),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        self.get_validated_participant_manager(
            meeting_manager=meeting_manager, meeting_participant_id=participant_id
        )

        token = self.generate_token(
            meeting_manager=meeting_manager, meeting_participant_id=participant_id
        )

        return StandardAPIResponse(
            data={"token": token},
            status=status.HTTP_201_CREATED,
        )


class MeetingParticipantInviteAPIView(MeetingParticipantMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [KeyCloakAuthentication]

    def post(self, request, *args, **kwargs):
        meeting_id = kwargs.pop("meeting_id")
        participant_id = kwargs.pop("participant_id")
        notification_type = request.data.get(
            "notification_type", NotificationType.CALL.value
        )

        meeting_manager = self.get_validated_meeting_manager(meeting_id=meeting_id)
        meeting_obj = meeting_manager.meeting_obj
        inviter_participant = self.get_validated_participant(
            meeting_obj=meeting_obj,
            user=self.request.user,
        )
        if inviter_participant is None:
            raise StandardAPIException(
                code="cannot_send_invite",
                detail=ERROR_DETAILS["cannot_send_invite"].format(
                    reason="user_not_a_participant"
                ),
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        participant_manager = self.get_validated_participant_manager(
            meeting_manager=meeting_manager, meeting_participant_id=participant_id
        )

        invite_response_data, invite_status_code = participant_manager.notify(
            inviter=inviter_participant, notification_type=notification_type
        )

        if not invite_status_code:
            raise StandardAPIException(
                code=invite_response_data,
                detail=ERROR_DETAILS.get(invite_response_data, invite_response_data),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return StandardAPIResponse(data=invite_response_data, status=invite_status_code)


class MeetingTokenGenerationAPIView(MeetingParticipantMixin, GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        meeting_id = request.data.get("meeting_id")
        meeting_participant_id = request.data.get("meeting_participant_id")
        staff_id = request.data.get("staff_id")
        patient_id = request.data.get("patient_id")

        meeting_manager = self.get_validated_meeting_manager(meeting_id=meeting_id)
        if meeting_participant_id is not None:
            self.get_validated_participant_manager(
                meeting_manager=meeting_manager,
                meeting_participant_id=meeting_participant_id,
            )
        if not meeting_participant_id and (staff_id or patient_id):
            meeting_participant = self.get_validated_meeting_participant(
                meeting_id=meeting_id, staff_id=staff_id, patient_id=patient_id
            )
            meeting_participant_id = str(meeting_participant.id)

        token = self.generate_token(
            meeting_manager=meeting_manager,
            meeting_participant_id=meeting_participant_id,
        )

        return StandardAPIResponse(
            data={"token": token},
            status=status.HTTP_201_CREATED,
        )


class MeetingEventsListenerAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    parser_classes = [WebhookJSONParser, JSONParser]

    @staticmethod
    def post(request, *args, **kwargs):
        event = request.data.get("event")
        sid = request.data.get("room", {}).get("sid")

        event_processor = MeetingEventProcessor(session_id=sid, event=event)
        event_processed = event_processor.process()

        return StandardAPIResponse(
            data=event_processed,
            status=(
                status.HTTP_200_OK if event_processed else status.HTTP_400_BAD_REQUEST
            ),
        )


class MeetingMessagesListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = MeetingMessageFilter
    ordering = ("-created_on",)
    permission_classes = [AllowAny]
    queryset = MeetingMessage.objects.all()
    serializer_class = MeetingMessageSerializer
    pagination_class = StandardPageNumberPagination
