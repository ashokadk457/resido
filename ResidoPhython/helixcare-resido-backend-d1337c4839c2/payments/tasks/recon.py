import uuid

from celery import shared_task
from django_tenants.utils import tenant_context

from customer_backend.managers.tenant import TenantManager
from common.utils.logging import logger


@shared_task
def transactions_recon(*args, **kwargs):
    try:
        task_id = transactions_recon.request.id.__str__()
    except Exception:
        task_id = str(uuid.uuid4())

    kwargs["task_id"] = task_id
    tenant_obj = TenantManager.init(**kwargs).tenant_obj
    with tenant_context(tenant_obj):
        from payments.managers.transaction.tasks.recon import (
            TransactionsReconciliationTask,
        )

        logger.info(f"Received message for transactions_recon - {kwargs}")
        recon_task_manager = TransactionsReconciliationTask(**kwargs)
        recon_task_manager.run()
