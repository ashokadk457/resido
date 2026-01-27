import json
import uuid

from django_celery_beat.models import PeriodicTask
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from customer_backend.managers.tenant import TenantManager
from common.response import StandardAPIResponse
from payments.tasks.recon import transactions_recon
from processflow.constants import ProcessTriggerType


class TriggerTxnReconTaskAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def post(request):
        tm = TenantManager()
        task_name = f"transactions_recon - {tm.tenant_schema_name}"
        task_obj = PeriodicTask.objects.filter(name=task_name).first()
        if task_obj is None:
            raise StandardAPIException(
                code="transaction_recon_job_not_found",
                detail=ERROR_DETAILS["transaction_recon_job_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )

        kwargs = json.loads(task_obj.kwargs)
        kwargs["process_trigger_type"] = ProcessTriggerType.ADHOC_VIA_API.value
        async_task = transactions_recon.apply_async(
            kwargs=kwargs, task_id=str(uuid.uuid4())
        )

        adhoc_async_task_id = str(async_task.id)
        response_data = {
            "message": "Triggered Transactions Recon Task!",
            "adhoc_async_task_id": adhoc_async_task_id,
        }
        return StandardAPIResponse(data=response_data, status=status.HTTP_202_ACCEPTED)
