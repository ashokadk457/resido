from rest_framework_simplejwt.tokens import AccessToken

from .backend import ResidentTokenBackend


class ResidentAccessToken(AccessToken):
    _token_backend = ResidentTokenBackend.init()

    @classmethod
    def for_tenant_resident(
        cls, tenant, resident, expiry=None, sub_token_type="full_access"
    ):
        token = cls()
        token["patient_id"] = str(resident.id)
        token["tenant_id"] = str(tenant.id)
        token["sub_token_type"] = sub_token_type
        if expiry:
            token["exp"] = expiry

        return token
