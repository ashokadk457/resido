from django.db import models

from audit.models import GenericModel
from common.models import optional
from customer_backend.models.rla import Module, SubModuleComposition
from subscriptions.constants import TierCode, TierMetricCode


class Tier(GenericModel):
    code = models.CharField(
        choices=TierCode.choices(),
        max_length=100,
        unique=True,
    )
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(**optional)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class TierMetric(GenericModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    submodule = models.ForeignKey(
        SubModuleComposition, on_delete=models.CASCADE, **optional
    )
    code = models.CharField(
        choices=TierMetricCode.choices(),
        max_length=100,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(**optional)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("module", "submodule", "code")

    def __str__(self):
        if self.submodule is None:
            return f"{self.module.__str__()}: {self.name}"

        return f"{self.module.__str__()}: {self.submodule.__str__()}: {self.name}"


class TierComposition(GenericModel):
    tier = models.ForeignKey(Tier, on_delete=models.CASCADE)
    tier_metric = models.ForeignKey(TierMetric, on_delete=models.CASCADE, **optional)
    value = models.CharField()
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("tier", "tier_metric")
