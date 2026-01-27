import os

from common.utils.enum import EnumWithValueConverter


class ProcessType(EnumWithValueConverter):
    PROCESS_BILL_REFUND_REQUEST = "PROCESS_BILL_REFUND_REQUEST"
    TRANSACTIONS_RECONCILIATION = "TRANSACTIONS_RECONCILIATION"
    VISIT_TYPE_ASSIGNMENT = "VISIT_TYPE_ASSIGNMENT"


class ProcessStatus(EnumWithValueConverter):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    RETRYING = "RETRYING"
    TIMED_OUT = "TIMED_OUT"


class ProcessTriggerType(EnumWithValueConverter):
    ADHOC_VIA_API = "ADHOC_VIA_API"
    PERIODIC = "PERIODIC"


RUNNING_PROCESS_TIME_THRESHOLD_IN_MINUTES = int(
    os.getenv("RUNNING_PROCESS_TIME_THRESHOLD_IN_MINUTES", "5")
)

LONG_RUNNING_PROCESS_ERROR_BODY = {
    "errors": [
        {
            "code": "process_terminated_by_system",
            "message": "The process was found to be long running and thus was terminated by the system",
        }
    ],
    "status": False,
}
