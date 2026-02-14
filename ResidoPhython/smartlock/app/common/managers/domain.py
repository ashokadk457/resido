from django.db.models import Manager


class DomainManager(Manager):
    def create_domain(self, domain_value, is_primary=False, tenant=None):
        domain = self.model(
            domain=domain_value,
            is_primary=is_primary,
            tenant=tenant,
        )
        domain.save()
        return domain
