from django.db import models

from audit.models import GenericModel
from common.models import optional, HealthCareCustomer
from subscriptions.constants import ProductSettingCategory


class ProductSetting(GenericModel):
    name = models.CharField(max_length=200, unique=True)
    visible_name = models.CharField(max_length=200, unique=True)
    category = models.CharField(
        choices=ProductSettingCategory.choices(),
        max_length=100,
        default=ProductSettingCategory.GENERAL.value,
    )
    description = models.TextField(**optional)
    default_value = models.CharField(max_length=512, **optional)
    seeded = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductSettingValue(GenericModel):
    customer = models.ForeignKey(HealthCareCustomer, on_delete=models.CASCADE)
    setting = models.ForeignKey(ProductSetting, on_delete=models.CASCADE)
    value = models.CharField(max_length=512)

    class Meta:
        unique_together = ("customer", "setting")

    def __str__(self):
        return f"{self.customer.__str__()}.{self.setting.name} = {self.value}"
