from rest_framework_simplejwt.authentication import JWTAuthentication

from common.utils.logging import logger
from helixauth.authentication.customer.onboarding import (
    CustomerOnboardingAuthentication,
)
from helixauth.authentication.kc import KeyCloakAuthentication


class CustomerCompositeAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super(CustomerCompositeAuthentication, self).__init__(*args, **kwargs)
        self.kc_auth = KeyCloakAuthentication(*args, **kwargs)
        self.onboard_auth = CustomerOnboardingAuthentication(*args, **kwargs)

    def authenticate(self, request):
        user, token = None, None
        try:
            user, token = self.kc_auth.authenticate(request=request)
        except Exception as e:
            logger.info(f"KC Auth Failed; {str(e)}")

            user, token = self.onboard_auth.authenticate(request=request)

        return user, token
