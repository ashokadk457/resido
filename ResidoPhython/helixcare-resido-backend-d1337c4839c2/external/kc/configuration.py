from external.kc.constants import (
    KEYCLOAK_BASE_URL,
    KEYCLOAK_MASTER_REALM,
    KEYCLOAK_MASTER_ADMIN_USERNAME,
    KEYCLOAK_MASTER_ADMIN_PASSWORD,
)


class KeyCloakConfiguration:
    @classmethod
    def init(cls, **kwargs):
        if kwargs.get("realm") == KEYCLOAK_MASTER_REALM:
            master_config = cls.get_master_config()
            return cls(**master_config)

        return cls()

    @classmethod
    def get_master_config(cls):
        return {
            "realm": KEYCLOAK_MASTER_REALM,
            "admin_username": KEYCLOAK_MASTER_ADMIN_USERNAME,
            "admin_password": KEYCLOAK_MASTER_ADMIN_PASSWORD,
        }

    def __init__(self, **kwargs):
        from customer_backend.managers.tenant import TenantManager

        self.tenant_manager = kwargs.get("tenant_manager", TenantManager())
        self.base_url = KEYCLOAK_BASE_URL
        self.realm = kwargs.get("realm", self.tenant_manager.tenant_realm)
        self.admin_username = kwargs.get(
            "admin_username", self.tenant_manager.tenant_realm_admin
        )
        self.admin_password = kwargs.get(
            "admin_password", self.tenant_manager.tenant_realm_password
        )
        self.client_id = kwargs.get("client_id", self.tenant_manager.tenant_client_id)
        self.client_secret = kwargs.get(
            "client_secret", self.tenant_manager.tenant_client_secret
        )
        self.client_uuid = kwargs.get(
            "client_uuid", self.tenant_manager.tenant_client_uuid
        )

    @property
    def all(self):
        return self.__dict__
