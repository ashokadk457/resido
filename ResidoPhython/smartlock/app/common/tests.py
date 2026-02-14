# Create your tests here.
from django.db import connection
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import get_tenant_model

from lookup.managers.lookup import LookupManager


class BaseTenantTestCase(TenantTestCase):
    @classmethod
    def setUpClass(cls):
        test_tenant = cls._get_test_tenant()
        if test_tenant:
            cls.tenant = test_tenant
            connection.set_tenant(cls.tenant)
            return
        super().setUpClass()
        cls.seed_initial_tenant_data()

    @classmethod
    def seed_initial_tenant_data(cls):
        LookupManager().populate_lookup()

    @classmethod
    def _get_test_tenant(cls) -> bool:
        tenant_model = get_tenant_model()
        return tenant_model.objects.filter(
            schema_name=cls.get_test_schema_name()
        ).first()

    @classmethod
    def setup_tenant(cls, tenant):
        tenant.code = 2578
        return tenant

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

    @classmethod
    def tearDownClass(cls):
        pass
