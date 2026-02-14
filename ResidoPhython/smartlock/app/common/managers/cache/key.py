from django.db import connection


def get_pulse_cache_key(key, key_prefix, version):
    tenant = connection.tenant
    key_prefix = getattr(tenant, "id", None)
    return f"{key_prefix}:{key}"
