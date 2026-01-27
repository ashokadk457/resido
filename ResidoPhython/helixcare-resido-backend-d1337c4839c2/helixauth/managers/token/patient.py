from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from helixauth.token.resident.access import ResidentAccessToken


class PatientTokenManager:
    @staticmethod
    def get_token_for_tenant_patient(tenant, patient, exp=None):
        access_token = ResidentAccessToken.for_tenant_resident(tenant, patient, exp)
        return str(access_token)

    @staticmethod
    def get_validated_token_from_raw(raw_token):
        return ResidentAccessToken(raw_token)

    @staticmethod
    def get_unverified_token_from_raw(token):
        return ResidentAccessToken(token, verify=False)

    @staticmethod
    def disable_all_tokens(tokens):
        all_token_objects = OutstandingToken.objects.filter(jti__in=tokens)
        all_blacklisted_token_objects = [
            BlacklistedToken(token=obj) for obj in all_token_objects
        ]
        BlacklistedToken.objects.bulk_create(
            objs=all_blacklisted_token_objects, ignore_conflicts=True
        )
