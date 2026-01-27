from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


class TokenManager:
    @staticmethod
    def disable_all_tokens(tokens):
        all_token_objects = OutstandingToken.objects.filter(jti__in=tokens)
        all_blacklisted_token_objects = [
            BlacklistedToken(token=obj) for obj in all_token_objects
        ]
        BlacklistedToken.objects.bulk_create(
            objs=all_blacklisted_token_objects, ignore_conflicts=True
        )
