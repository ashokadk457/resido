from django_tenants.middleware import TenantMainMiddleware
from django_tenants.utils import get_tenant_domain_model


class StandardTenantMiddleware(TenantMainMiddleware):
    @staticmethod
    def get_public_domain():
        domain_model = get_tenant_domain_model()
        public_domain_obj = domain_model.objects.filter(
            tenant__schema_name="public"
        ).first()
        return public_domain_obj.domain if public_domain_obj else None

    def hostname_from_request(self, request):
        if request.path.startswith("/api/v1/versions"):
            return self.get_public_domain()
        return super().hostname_from_request(request=request)
