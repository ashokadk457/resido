from django.core.management.base import BaseCommand

from customer_backend.managers.tenant import TenantManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")
        parser.add_argument("name", type=str, help="Name")
        parser.add_argument("tenant_url", type=str, help="Tenant URL")
        parser.add_argument(
            "realm_suffix", type=str, help="KC Realm Suffix", default=None
        )

    @classmethod
    def launch_tenant(cls, **kwargs):
        tm = TenantManager()
        tm.launch_new_tenant(**kwargs)

    def handle(self, *args, **options):
        schema_name = options["schema"]
        tenant_name = options["name"]
        tenant_domain = options["tenant_url"]
        realm_suffix = options.get("realm_suffix")
        kwargs = {
            "schema_name": schema_name,
            "tenant_name": tenant_name,
            "tenant_domain": tenant_domain,
            "realm_suffix": realm_suffix,
        }

        return self.launch_tenant(**kwargs)
