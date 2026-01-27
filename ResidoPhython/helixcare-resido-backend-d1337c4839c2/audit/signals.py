from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.db import models
from django.db.migrations.recorder import MigrationRecorder
from audit.models import AuditEvent, Audit
from common.managers.feature.switch import FeatureSwitchManager
from common.thread_locals import get_current_user, get_request
from helixauth.models import ModuleComposition
from django_tenants.utils import tenant_context, get_tenant_model
from django.apps import apps

EXCLUDED_MODELS = [
    "Audit",
    "AuditEvent",
    "AccessLog",
    "RegisteredDevice",
    "OutstandingToken",
    "NotificationQueue",
    "Lookup",
    "Response",
    "Request",
    "SQLQuery",
    "Profile",
    "SQLQueryManager",
    "HealthCareCustomer",
    "Domain",
    "DataMigrationExecution",
    "Site",
]

EXCLUDED_FIELDS = [
    "created_on",
    "updated_on",
    "created_by",
    "updated_by",
    "deleted_by",
    "version",
    "id",
]


def get_user():
    from helixauth.models import HelixUser

    current_user = get_current_user()
    if not isinstance(current_user, HelixUser):
        return None
    return current_user


def get_ip():
    request = get_request()
    if request:
        request_meta = request.META
        x_forwarded_for = request_meta.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(",")[0]
        else:
            ip_address = request_meta.get("REMOTE_ADDR")
        return ip_address
    else:
        return None


def get_module(entity):
    comp = ModuleComposition.objects.filter(entity=entity).first()
    return comp.module.name if comp else None


def check_model_excluded(model):
    if model in EXCLUDED_MODELS:
        return True
    tenant = get_tenant_model().objects.get(schema_name="public")
    with tenant_context(tenant):
        all_models_in_tenant = apps.get_models()
        if model in all_models_in_tenant:
            return True
    return False


def check_field_excluded(field):
    return field in EXCLUDED_FIELDS


def log_audit_event(sender, instance, action):
    if not FeatureSwitchManager(feature_switch_name="audit").is_feature_active():
        return

    event = None
    user = get_user()
    ip = get_ip()
    module = get_module(sender.__name__)
    for field in instance._meta.get_fields():
        if isinstance(field, models.Field):
            old_value = None
            new_value = getattr(instance, field.name)

            if action != "create":
                old_value = getattr(sender.objects.get(pk=instance.pk), field.name)

            if not check_field_excluded(field.name) and old_value != new_value:
                if event is None:
                    event = AuditEvent.objects.create(
                        table=sender.__name__,
                        key=instance.pk,
                        action=action,
                        created_by=user,
                        ip_address=ip,
                        module=module,
                    )
                Audit.objects.create(
                    field=field.name,
                    old_value=old_value,
                    new_value=new_value,
                    event=event,
                )


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # if sender == MigrationRecorder.Migration:
    #     return
    # if check_model_excluded(sender.__name__):
    #     return
    # if created:
    #     log_audit_event(sender, instance, "create")
    pass


@receiver(pre_save)
def model_updated(sender, instance, **kwargs):
    # if sender == MigrationRecorder.Migration:
    #     return
    # if check_model_excluded(sender.__name__):
    #     return
    # try:
    #     sender.objects.get(pk=instance.pk)
    #     log_audit_event(sender, instance, "update")
    # except ObjectDoesNotExist:
    pass


@receiver(pre_delete)
def model_deleted(sender, instance, **kwargs):
    if sender == MigrationRecorder.Migration:
        return
    if check_model_excluded(sender.__name__):
        return
    log_audit_event(sender, instance, "delete")
