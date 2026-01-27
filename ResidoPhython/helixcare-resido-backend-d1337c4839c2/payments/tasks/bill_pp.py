from celery import shared_task
from django_tenants.utils import tenant_context
from common.utils.logging import logger
from common.tasks import BaseTaskWithRetry
from common.models import HealthCareCustomer
from payments.managers.bill_pp import BillPaymentPlanManager


@shared_task(
    name="trigger_bill_plans_payment",
    bind=True,
    base=BaseTaskWithRetry,
)
def trigger_bill_plans_payment(self, *args, **kwargs):
    for tenant in HealthCareCustomer.objects.all():
        try:
            logger.info(
                f"Starting trigger_bill_plans_payment task for tenant with schema {tenant.schema_name}"
            )
            with tenant_context(tenant):
                (
                    total,
                    success,
                    failed,
                ) = BillPaymentPlanManager.process_bill_plan_payments()
                logger.info(
                    f"Completed running trigger_bill_plans_payment task for tenant with schema {tenant.schema_name}. Total: {total}, Success: {success}, Failed: {failed}"
                )
        except Exception as e:
            logger.info(
                f"Exception while running trigger_bill_plans_payment task for tenant with schema {tenant.schema_name}, Ereor: {e}"
            )
