import jwt
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import InvalidToken
from django.contrib.auth.models import AnonymousUser
from common.thread_locals import set_current_user
from helixauth.authentication.resident.base import BaseResidentAuthentication
from helixauth.managers.token.patient import PatientTokenManager


class GuestPatientAuthentication(BaseResidentAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return AnonymousUser(), None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return AnonymousUser(), None

        unverified_payload = jwt.decode(
            jwt=raw_token, options={"verify_signature": False}
        )
        is_guest_patient_token = self.check_sub_token_type(
            unverified_payload, required_sub_token_type="guest_patient"
        )
        if not is_guest_patient_token:
            raise InvalidToken(_("Token is not guest patient token"))

        validated_token = PatientTokenManager.get_validated_token_from_raw(raw_token)
        patient = self.get_resident(validated_token, request.tenant)
        user = patient.user
        set_current_user(user)
        request.is_resident = True
        request.patient = patient
        return user, validated_token
