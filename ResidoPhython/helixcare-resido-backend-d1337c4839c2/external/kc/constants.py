import os

KEYCLOAK_BASE_URL = os.getenv("KEYCLOAK_BASE_URL", "https://identity-qa.helixbeat.com")
KEYCLOAK_MASTER_REALM = os.getenv("KEYCLOAK_MASTER_REALM", "master")
KEYCLOAK_MASTER_ADMIN_USERNAME = os.getenv("KEYCLOAK_MASTER_ADMIN_USERNAME", "admin")
KEYCLOAK_MASTER_ADMIN_PASSWORD = os.getenv(
    "KEYCLOAK_MASTER_ADMIN_PASSWORD", "5fq3MGLeVuQWb07"
)
KEYCLOAK_REALMSUPERADMIN_USERNAME = os.getenv(
    "KEYCLOAK_REALMSUPERADMIN_USERNAME", "realmsuperadmin"
)
KEYCLOAK_REALMSUPERADMIN_USER_DATA = {
    "email": f"{KEYCLOAK_REALMSUPERADMIN_USERNAME}@helixbeat.com",
    "username": KEYCLOAK_REALMSUPERADMIN_USERNAME,
    "first_name": "The Admin",
    "last_name": "Of Realm",
    "email_verified": True,
}
KEYCLOAK_REALMSUPERADMIN_PASSWORD = "admin"
KEYCLOAK_REALMSUPERADMIN_CLIENT_ID_TO_ROLE_NAMES_MAP = {
    "account": [
        "delete-account",
        "manage-account",
        "manage-account-links",
        "manage-consent",
        "view-applications",
        "view-consent",
        "view-groups",
        "view-profile",
    ],
    "broker": ["read-token"],
    "realm-management": [
        "create-client",
        "impersonation",
        "manage-authorization",
        "manage-clients",
        "manage-events",
        "manage-identity-providers",
        "manage-realm",
        "manage-users",
        "query-clients",
        "query-groups",
        "query-realms",
        "query-users",
        "realm-admin",
        "view-authorization",
        "view-clients",
        "view-events",
        "view-identity-providers",
        "view-realm",
        "view-users",
    ],
}
