from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context
from faker import Faker

from customer_backend.managers.tenant import TenantManager

fake = Faker()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")
        parser.add_argument("email", type=str, help="Email")
        parser.add_argument("password", type=str, help="Password")
        parser.add_argument("first_name", type=str, help="First Name")
        parser.add_argument("last_name", type=str, help="Last Name")

    def handle(self, *args, **options):
        schema_name = options["schema"]
        email = options["email"]
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]

        tm = TenantManager.init(schema_name=schema_name)
        with tenant_context(tm.tenant_obj):
            tm.create_default_site_admin(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
