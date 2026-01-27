from django.db import models

from assets.utils import PathAndRename
from audit.models import GenericModel

optional = {"null": True, "blank": True}


class Asset(GenericModel):
    TYPE_CHOICES = (("image", "image"), ("doc", "doc"))

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, **optional)
    file = models.FileField(upload_to=PathAndRename("assets"))
    filename = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        # if not self.created_by:
        #     self.created_by = get_current_user()
        super().save(*args, **kwargs)
