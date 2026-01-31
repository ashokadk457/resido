from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

class BearerTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        print(f"Authorization Header: {auth_header}")

        if not auth_header:
            raise AuthenticationFailed('Missing Authorization header')

        prefix, token = auth_header.split()

        print(f"Prefix: {prefix}, Token: {token}")
        if prefix.lower() != 'bearer':
            raise AuthenticationFailed('Invalid token type')

        return (AnonymousUser(), token)
