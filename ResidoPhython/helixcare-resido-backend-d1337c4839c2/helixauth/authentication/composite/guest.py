from rest_framework_simplejwt.authentication import JWTAuthentication

from common.utils.logging import logger
from helixauth.authentication.resident.guest import GuestPatientAuthentication
from helixauth.authentication.resident.rental_request import (
    ResidentRentalRequestAuthentication,
)
from helixauth.authentication.user.reset_password import RentalApplicationAuthentication
from helixauth.authentication.kc import KeyCloakAuthentication


class GuestCompositeAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super(GuestCompositeAuthentication, self).__init__(*args, **kwargs)
        self.kc_auth = KeyCloakAuthentication(*args, **kwargs)
        self.guest_patient_auth = GuestPatientAuthentication(*args, **kwargs)

    def authenticate(self, request):
        try:
            user, token = self.kc_auth.authenticate(request=request)
        except Exception as e:
            logger.info(f"KC Authentication Failed; {str(e)}")
            user, token = self.guest_patient_auth.authenticate(request=request)

        return user, token


class ResidentCompositeAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super(ResidentCompositeAuthentication, self).__init__(*args, **kwargs)
        self.kc_auth = KeyCloakAuthentication(*args, **kwargs)
        self.guest_resident_auth = RentalApplicationAuthentication(*args, **kwargs)
        self.rental_request_auth = ResidentRentalRequestAuthentication(*args, **kwargs)

    def authenticate(self, request):
        try:
            result = self.kc_auth.authenticate(request)
            if result is not None:
                return result
        except Exception as e:
            logger.info(f"KC Authentication Failed; {str(e)}")

        result = self.guest_resident_auth.authenticate(request)
        if result is not None:
            return result

        try:
            result = self.rental_request_auth.authenticate(request)
            if result is not None:
                return result
        except Exception as e:
            logger.info(f"Rental Request Authentication Failed; {str(e)}")

        return None
