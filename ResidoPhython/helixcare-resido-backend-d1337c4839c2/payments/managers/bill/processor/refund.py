from celery import shared_task
from django_tenants.utils import tenant_context

from customer_backend.managers.tenant import TenantManager
from payments.managers.bill.core import BillManager
from processflow.managers.process.processor.base import BaseAsyncTaskProcessor


class BillRefundProcessor(BaseAsyncTaskProcessor):
    def __init__(self, process_id, request_id, process_type, **kwargs):
        super(BillRefundProcessor, self).__init__(
            process_id=process_id,
            request_id=request_id,
            process_type=process_type,
            **kwargs,
        )

    @staticmethod
    @shared_task
    def process(**kwargs):
        kwargs["task_id"] = BillRefundProcessor.process.request.id.__str__()
        with tenant_context(TenantManager.init(**kwargs).tenant_obj):
            BillRefundProcessor._process(**kwargs)

    @classmethod
    def process_refund_request(cls, **kwargs):
        from payments.managers.bill.refund.request import BillRefundRequestManager

        refund_manager = BillRefundRequestManager(**kwargs)
        refund_manager.get_refund_and_related_objects()
        return refund_manager.refund()

    @classmethod
    def update_bill(cls, bill_refund_obj):
        bill_obj = bill_refund_obj.bill
        bill_manager = BillManager(bill_obj=bill_obj)
        bill_manager.update_bill_upon_refund(bill_refund_obj=bill_refund_obj)

    @classmethod
    def _run(cls, **kwargs):
        status, error_body, error_code = True, None, None
        status, bill_refund_obj = cls.process_refund_request(**kwargs)
        cls.update_bill(bill_refund_obj=bill_refund_obj)
        return status, error_body, error_code
