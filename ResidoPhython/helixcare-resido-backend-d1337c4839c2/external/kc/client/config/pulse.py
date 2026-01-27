class PULSEConfig:
    PULSE_CLIENT_CONFIG = {
        "clientId": "pulse",
        "name": "PULSE",
        "description": "Base Client for PULSE",
        "rootUrl": "http://demo.localhost.com:8001",
        "adminUrl": "http://demo.localhost.com:8001",
        "baseUrl": "http://demo.localhost.com:8001/admin",
        "surrogateAuthRequired": False,
        "enabled": True,
        "alwaysDisplayInConsole": True,
        "clientAuthenticatorType": "client-secret",
        "secret": "4RfSaPHjPmizCl2RZN6GC1iHCVhd6yqK",
        "redirectUris": ["http://demo.localhost.com:8001/*"],
        "webOrigins": ["http://demo.localhost.com:8001"],
        "notBefore": 0,
        "bearerOnly": False,
        "consentRequired": False,
        "standardFlowEnabled": True,
        "implicitFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "serviceAccountsEnabled": False,
        "publicClient": False,
        "frontchannelLogout": True,
        "protocol": "openid-connect",
        "attributes": {
            "client.secret.creation.time": "1738319747",
            "client.introspection.response.allow.jwt.claim.enabled": "false",
            "oauth2.device.authorization.grant.enabled": "true",
            "backchannel.logout.revoke.offline.tokens": "false",
            "use.refresh.tokens": "true",
            "oidc.ciba.grant.enabled": "false",
            "client.use.lightweight.access.token.enabled": "false",
            "backchannel.logout.session.required": "true",
            "client_credentials.use_refresh_token": "false",
            "tls.client.certificate.bound.access.tokens": "false",
            "require.pushed.authorization.requests": "false",
            "acr.loa.map": "{}",
            "display.on.consent.screen": "false",
            "token.response.type.bearer.lower-case": "false",
        },
        "authenticationFlowBindingOverrides": {},
        "fullScopeAllowed": True,
        "nodeReRegistrationTimeout": -1,
        "defaultClientScopes": [
            "web-origins",
            "acr",
            "roles",
            "profile",
            "basic",
            "email",
        ],
        "optionalClientScopes": [
            "address",
            "phone",
            "offline_access",
            "microprofile-jwt",
        ],
        "access": {"view": True, "configure": True, "manage": True},
    }

    def __init__(self):
        self.data = self.PULSE_CLIENT_CONFIG
        self.client_uuid = None

    @property
    def client_id(self):
        return self.data["clientId"]

    @property
    def client_secret(self):
        return self.data["secret"]
