from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.settings import api_settings

from common.stores.key import key_store


class ResidentTokenBackend(TokenBackend):
    @classmethod
    def init(cls):
        return ResidentTokenBackend(
            algorithm=api_settings.ALGORITHM,
            signing_key=key_store.tn_auth_private_key,
            verifying_key=key_store.tn_auth_public_key,
            audience=api_settings.AUDIENCE,
            issuer=api_settings.ISSUER,
            jwk_url=api_settings.JWK_URL,
            leeway=api_settings.LEEWAY,
        )

    def __init__(self, **kwargs):
        super(ResidentTokenBackend, self).__init__(**kwargs)
