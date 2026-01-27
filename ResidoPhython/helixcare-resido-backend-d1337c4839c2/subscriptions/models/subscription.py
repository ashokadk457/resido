from django.db import models

from audit.models import GenericModel
from common.models import optional, HealthCareCustomer
from subscriptions.models.plan import Plan
from subscriptions.models.tier import Tier


class TenantSubscription(GenericModel):
    tenant = models.ForeignKey(HealthCareCustomer, on_delete=models.CASCADE, **optional)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE, **optional)
    start_date = models.DateTimeField(**optional)
    end_date = models.DateTimeField(**optional)
    expires_on = models.DateTimeField(**optional)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tenant", "plan")
