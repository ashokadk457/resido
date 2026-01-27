from django.core.management.base import BaseCommand
from django_tenants.utils import tenant_context

from customer_backend.managers.tenant import TenantManager
from common.models import HealthCareCustomer


class Command(BaseCommand):
    @classmethod
    def create_additional_domain_for_public(cls):
        tm = TenantManager()
        tm.create_additional_domain_for_public_tenant()

    def handle(self, *args, **options):
        with tenant_context(HealthCareCustomer.objects.get(schema_name="public")):
            return self.create_additional_domain_for_public()
