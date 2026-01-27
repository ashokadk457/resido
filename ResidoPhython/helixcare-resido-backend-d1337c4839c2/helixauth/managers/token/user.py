from helixauth.token.user.access import HelixUserAccessToken
from staff.managers.helixstaff import HelixStaffManager


class HelixUserTokenManager:
    @staticmethod
    def get_validated_token_from_raw(raw_token):
        return HelixUserAccessToken(raw_token)

    @staticmethod
    def get_staff(user):
        return HelixStaffManager.get_by(user=user)
