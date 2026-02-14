import jwt
from datetime import datetime


class BaseAccessLogManager:
    @staticmethod
    def get_details_from_refresh_token(refresh_token):
        if not refresh_token:
            return None, None

        unverified_payload = jwt.decode(
            jwt=refresh_token, options={"verify_signature": False}
        )
        jti = unverified_payload["jti"]
        exp = unverified_payload["exp"]
        exp_obj = datetime.fromtimestamp(exp)
        return jti, exp_obj
