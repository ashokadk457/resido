from drf_spectacular.extensions import OpenApiAuthenticationExtension

class BearerAuthScheme(OpenApiAuthenticationExtension):
    target_class = 'app.auth.authentication.BearerTokenAuthentication'
    name = 'BearerAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
        }