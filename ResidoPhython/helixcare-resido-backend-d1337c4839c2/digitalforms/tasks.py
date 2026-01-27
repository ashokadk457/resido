from celery import shared_task
from celery.utils.log import get_task_logger
from django_tenants.utils import get_tenant_model, tenant_context
from common.tasks import BaseTaskWithRetry
from digitalforms.managers.form_version import FormVersionManager

logger = get_task_logger(__name__)


@shared_task(
    name="auto_approve_forms_task",
    bind=True,
    base=BaseTaskWithRetry,
)
def auto_approve_forms_task():
    for tenant in get_tenant_model().objects.exclude(schema_name="public"):
        with tenant_context(tenant):
            logger.info(f"Starting auto_approve_forms_task for tenant {tenant.name}")
            FormVersionManager.check_auto_approval_form_versions()
            logger.info(f"Finished auto_approve_forms_task for tenant {tenant.name}")
