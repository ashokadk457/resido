from django.db import models

from audit.models import GenericModel
from common.models import optional
from customer_backend.models.rla import Module, SubModuleComposition
from subscriptions.constants import ProductPlanCode


class Plan(GenericModel):
    MODEL_ALL_DATA_CACHE_KEY = "PLANS"

    code = models.CharField(
        choices=ProductPlanCode.choices(),
        max_length=100,
    )
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    seeded = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PlanModuleComposition(GenericModel):
    MODEL_ALL_DATA_CACHE_KEY = "PLAN_MODULE_COMPOSITIONS"

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    submodule = models.ForeignKey(
        SubModuleComposition, on_delete=models.CASCADE, **optional
    )
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("plan", "module", "submodule")

    def __str__(self):
        if self.submodule is None:
            return f"{self.plan.__str__()}: {self.module.__str__()}"

        return f"{self.plan.__str__()}: {self.module.__str__()}: {self.submodule.__str__()}"
