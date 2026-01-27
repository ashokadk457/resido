from django.db import models

from common.models import GenericModel, optional

from common.utils.general import (
    get_display_id,
)


class ReasonCategory(GenericModel):
    policy_name = models.CharField(max_length=250, unique=True)
    status = models.BooleanField(default=True)


class Reason(GenericModel):
    category = models.ForeignKey(
        ReasonCategory, related_name="reason_category", on_delete=models.CASCADE
    )
    display_id = models.CharField(max_length=100)
    name = models.CharField(max_length=250)
    description = models.TextField(**optional)
    status = models.BooleanField(default=True)

    class Meta:
        unique_together = ("category", "name")

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "BPC")
        super(Reason, self).save(*args, **kwargs)
