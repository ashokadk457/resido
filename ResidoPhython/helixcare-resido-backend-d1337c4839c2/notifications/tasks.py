from notifications.helix_notification_handler import HelixNotificationHandler
from resido.celery import app
from django_tenants.utils import get_tenant_model, tenant_context
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@app.task
def send_notification():
    for tenant in get_tenant_model().objects.exclude(schema_name="public"):
        with tenant_context(tenant):
            logger.info("Sending... Notifications")
            try:
                HelixNotificationHandler().consume()
            except Exception as e:
                logger.error(
                    f"Exception while sending notifications for tenant: {tenant}, error: {e}"
                )
