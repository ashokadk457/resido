from rest_framework_simplejwt.tokens import AccessToken

from .backend import HelixUserTokenBackend


class HelixUserAccessToken(AccessToken):
    _token_backend = HelixUserTokenBackend.init()

    @classmethod
    def add_common_fields(
        cls, token, tenant, expiry=None, sub_token_type="full_access"
    ):
        token["tenant_id"] = str(tenant.id)
        token["sub_token_type"] = sub_token_type
        if expiry:
            token["exp"] = expiry
        return token

    @classmethod
    def for_customer_onboarding(
        cls, tenant, user, expiry=None, sub_token_type="customer_onboarding"
    ):
        token = cls()
        token["user_id"] = user.get("email", "")
        return cls.add_common_fields(token, tenant, expiry, sub_token_type)

    @classmethod
    def for_reset_password(
        cls, tenant, user, expiry=None, sub_token_type="reset_password"
    ):
        token = cls()
        token["user_id"] = str(user.id)
        return cls.add_common_fields(token, tenant, expiry, sub_token_type)

    @classmethod
    def for_rental_application_view(
        cls, tenant, user, expiry=None, sub_token_type="rental_application_view"
    ):
        token = cls()
        token["user_id"] = str(user.user.id)
        return cls.add_common_fields(token, tenant, expiry, sub_token_type)
