import uuid

from concurrency.fields import IntegerVersionField
from django.conf import settings
from django.db import models

from common.managers.model.generic import GenericModelManager
from common.constants import (
    RLA_WHITELISTED_MODELS,
    RLA_CHECK_ENFORCED,
)
from common.thread_locals import get_current_user

optional = {"null": True, "blank": True}


class GenericModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **optional,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **optional,
        related_name="+",
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **optional,
        related_name="+",
    )
    version = IntegerVersionField()

    objects = GenericModelManager()

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if (
            RLA_CHECK_ENFORCED
            and not hasattr(cls._meta, "path_to_location")
            and cls.__name__ not in RLA_WHITELISTED_MODELS
        ):
            raise NotImplementedError(
                f"RLA not implemented for model {cls.__name__}. Please implement or whitelist the model to skip checks."
            )

    def set_created_by_and_updated_by(self):
        from helixauth.models import HelixUser

        current_user = get_current_user()
        if not isinstance(current_user, HelixUser):
            return

        if self._state.adding:
            self.created_by = get_current_user()
        self.updated_by = get_current_user()

    def save(self, *args, **kwargs):
        self.set_created_by_and_updated_by()
        return super().save(*args, **kwargs)

    def get(self, attr):
        return self.__getattribute__(attr)

    def delete(self, *args, **kwargs):
        self.deleted_by = get_current_user()
        self.save()


class NameActiveGenericModel(GenericModel):
    name = models.CharField(unique=True, max_length=255)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class CodedModel(GenericModel):
    code = models.CharField(max_length=256, **optional)
    version = models.CharField(max_length=256, **optional)
    display_name = models.CharField(max_length=256, **optional)
    code_system = models.CharField(max_length=256, **optional)
    code_system_oid = models.CharField(max_length=256, **optional)

    class Meta:
        abstract = True


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    table = models.CharField(max_length=255)
    key = models.CharField(max_length=255, **optional)
    action = models.CharField(
        max_length=10,
        choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete")],
    )
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        **optional,
        related_name="+",
    )
    ip_address = models.CharField(max_length=255, **optional)
    module = models.CharField(max_length=255, **optional)

    def __str__(self):
        return f"{self.table} - {self.action} - {self.created_on}"


class Audit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    event = models.ForeignKey(AuditEvent, on_delete=models.CASCADE)
