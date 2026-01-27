from keycloak import KeycloakAdmin, KeycloakOpenID

from common.utils.logging import logger
from common.utils.requests import helix_request
from external.kc.client.config.pulse import PULSEConfig
from external.kc.configuration import KeyCloakConfiguration
from external.kc.constants import (
    KEYCLOAK_REALMSUPERADMIN_USER_DATA,
    KEYCLOAK_REALMSUPERADMIN_PASSWORD,
    KEYCLOAK_REALMSUPERADMIN_CLIENT_ID_TO_ROLE_NAMES_MAP,
    KEYCLOAK_MASTER_REALM,
    KEYCLOAK_REALMSUPERADMIN_USERNAME,
)


class KeyCloak:
    TOKEN_ENDPOINT = "/realms/{realm}/protocol/openid-connect/token"
    IMPERSONATION_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"

    @classmethod
    def init(cls, config=None, init_admin=True, init_openid=True, **kwargs):
        if kwargs.get("realm") == KEYCLOAK_MASTER_REALM:
            config = KeyCloakConfiguration.init(realm=KEYCLOAK_MASTER_REALM)

        return cls(
            config=config,
            init_admin=init_admin,
            init_openid=init_openid,
        )

    def __init__(
        self,
        config=None,
        init_admin=True,
        init_openid=True,
    ):
        self.config = config or KeyCloakConfiguration.init()
        self.init_admin = init_admin
        self.init_openid = init_openid
        self.admin = None
        self.openid = None
        if init_admin:
            self.admin = KeycloakAdmin(
                server_url=self.config.base_url,
                realm_name=self.config.realm,
                username=self.config.admin_username,
                password=self.config.admin_password,
            )

        if init_openid:
            self.openid = KeycloakOpenID(
                server_url=self.config.base_url,
                realm_name=self.config.realm,
                client_id=self.config.client_id,
                client_secret_key=self.config.client_secret,
            )

    def delete_user(self, auth_user_id):
        return self.admin.delete_user(auth_user_id)

    def assign_roles(
        self, auth_user_id, role_names, client_id_for_role_assignment, roles_data=None
    ):
        client_id_for_role_assignment = (
            client_id_for_role_assignment or self.config.client_uuid
        )

        roles_data = roles_data if roles_data is not None else []
        if not roles_data and role_names:
            roles_data = [
                self.admin.get_client_role(
                    client_id=client_id_for_role_assignment, role_name=role_name
                )
                for role_name in role_names
            ]

        self.admin.assign_client_role(
            user_id=auth_user_id,
            client_id=client_id_for_role_assignment,
            roles=roles_data,
        )

    def get_client_uuid_to_roles_map(self, client_id_to_roles_map):
        client_uuid_to_roles_map = {}
        for client_id, role_names in client_id_to_roles_map.items():
            client_uuid = str(self.admin.get_client_id(client_id=client_id))
            roles_data = [
                self.admin.get_client_role(client_id=client_uuid, role_name=role_name)
                for role_name in role_names
            ]
            client_uuid_to_roles_map[client_uuid] = roles_data

        return client_uuid_to_roles_map

    def assign_bulk_client_roles(self, auth_user_id, client_id_to_roles_map):
        logger.info(
            f"Bulk Assigning roles to {auth_user_id} ; {client_id_to_roles_map}"
        )
        client_uuid_to_roles_map = self.get_client_uuid_to_roles_map(
            client_id_to_roles_map=client_id_to_roles_map
        )
        for client_uuid, roles_data in client_uuid_to_roles_map.items():
            self.admin.assign_client_role(
                user_id=auth_user_id, client_id=client_uuid, roles=roles_data
            )

    def create_client(self, **kwargs):
        if not kwargs.get("client_id"):
            return

        create_client_payload = {
            "clientId": kwargs.get("client_id"),
            "name": kwargs.get("name"),
            "description": kwargs.get("description"),
            "rootUrl": kwargs.get("root_url"),
            "adminUrl": kwargs.get("admin_url"),
            "baseUrl": kwargs.get("base_url"),
            # "secret": kwargs.get("client_secret"),
            "alwaysDisplayInConsole": True,
            "redirectUris": kwargs.get("redirect_uris", ["/*"]),
            "webOrigins": kwargs.get("web_origins", ["/*"]),
            "standardFlowEnabled": True,
            "implicitFlowEnabled": True,
            "directAccessGrantsEnabled": kwargs.get(
                "direct_access_grants_enabled", True
            ),
            "serviceAccountsEnabled": True,
            "authorizationServicesEnabled": not kwargs.get("is_public_client", False),
            "publicClient": kwargs.get("is_public_client", False),
            "protocol": "openid-connect",
            "access": {"view": True, "configure": True, "manage": True},
            # "attributes": kwargs.get("attributes", {}),
        }
        if kwargs.get("client_secret") is not None:
            create_client_payload["secret"] = kwargs.get("client_secret")
        if kwargs.get("client_authenticator_type") is not None:
            create_client_payload["clientAuthenticatorType"] = kwargs.get(
                "client_authenticator_type"
            )
        if kwargs.get("consent_required") is not None:
            create_client_payload["consentRequired"] = kwargs.get("consent_required")
        if kwargs.get("default_client_scopes", []):
            create_client_payload["defaultClientScopes"] = kwargs.get(
                "default_client_scopes"
            )
        if kwargs.get("optional_client_scopes", []):
            create_client_payload["optionalClientScopes"] = kwargs.get(
                "optional_client_scopes"
            )

        if kwargs.get("attributes", {}):
            attributes = kwargs.get("attributes", {})
            attributes.pop("additional_default_redirect_urls", None)
            create_client_payload["attributes"] = attributes

        return self.admin.create_client(payload=create_client_payload)

    def signup_user(self, user_data, password):
        logger.info(f"Creating new user in KC: {user_data}")
        # TODO allow making phone number as username
        new_user_payload = {
            "email": user_data.get("email"),
            "username": (
                user_data.get("username")
                if user_data.get("username")
                else user_data.get("email")
            ),
            "enabled": True,
            "firstName": user_data.get("first_name"),
            "lastName": user_data.get("last_name"),
        }
        if password:
            new_user_payload["credentials"] = [
                {"type": "password", "value": password, "temporary": False}
            ]

        if user_data.get("extra_data"):
            new_user_payload["attributes"] = {
                k: [v] for k, v in user_data.get("extra_data", {}).items()
            }

        if user_data.get("email_verified"):
            new_user_payload["emailVerified"] = True

        auth_user_id = self.admin.create_user(payload=new_user_payload)
        return auth_user_id

    def update_user(self, user_obj):
        if not user_obj or (user_obj and not user_obj.auth_user_id):
            return

        update_user_payload = {
            "email": user_obj.email,
            "enabled": True,
            "firstName": user_obj.first_name,
            "lastName": user_obj.last_name,
        }
        auth_user_id = user_obj.auth_user_id

        return self.admin.update_user(user_id=auth_user_id, payload=update_user_payload)

    def logout_user(self, refresh_token):
        return self.openid.logout(refresh_token=refresh_token)

    def refresh_tokens(self, refresh_token):
        return self.openid.refresh_token(refresh_token=refresh_token)

    @property
    def token_url(self):
        url = f"{self.config.base_url}{self.TOKEN_ENDPOINT}"
        return url.format(realm=self.config.realm)

    def login(self, username, password=None):
        if password:
            return self.login_user(username=username, password=password)

        return self.impersonate_user(username=username)

    def login_user(self, username, password):
        return self.openid.token(username=username, password=password)

    def _create_realm(self, **kwargs):
        logger.info(f"Creating realm in KC - {kwargs.get('realm')}")
        new_realm_payload = {
            "realm": kwargs.get("realm"),
            "enabled": True,
            "userManagedAccessAllowed": True,
        }
        self.admin.create_realm(new_realm_payload)
        return kwargs.get("realm")

    def _create_realmsuperadmin(self, **kwargs):
        auth_user_id = self.signup_user(
            user_data=KEYCLOAK_REALMSUPERADMIN_USER_DATA,
            password=KEYCLOAK_REALMSUPERADMIN_PASSWORD,
        )
        self.assign_bulk_client_roles(
            auth_user_id=auth_user_id,
            client_id_to_roles_map=KEYCLOAK_REALMSUPERADMIN_CLIENT_ID_TO_ROLE_NAMES_MAP,
        )

    def _create_pulse_client(self, payload):
        return self.admin.create_client(payload=payload)

    def setup_realm_for_tenant(self, **kwargs):
        logger.info(
            "Setting up KC realm for the tenant. Make sure the KeyCloak is initialized with the master realm"
        )
        realm_name = self._create_realm(**kwargs)

        self.admin.change_current_realm(realm_name=realm_name)

        pulse_config = PULSEConfig()
        pulse_config.client_uuid = self._create_pulse_client(payload=pulse_config.data)
        self._create_realmsuperadmin(**kwargs)
        logger.info("Realm Setup Completed")

        return {
            "realm": realm_name,
            "client_id": pulse_config.client_id,
            "client_secret": pulse_config.client_secret,
            "client_uuid": pulse_config.client_uuid,
            "realm_admin": KEYCLOAK_REALMSUPERADMIN_USERNAME,
            "realm_password": KEYCLOAK_REALMSUPERADMIN_PASSWORD,
        }

    def impersonate_user(self, username):
        payload = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": self.IMPERSONATION_GRANT,
            "requested_subject": username,
        }

        response, _ = helix_request.post(url=self.token_url, data=payload)

        if response is not None and response.status_code == 200:
            return response.json()

        return {}
