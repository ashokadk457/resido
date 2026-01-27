from processflow.constants import ProcessType


class ProcessorFactory:
    def __init__(self, process_type=None):
        from payments.managers.bill.processor.refund import BillRefundProcessor
        from scheduling.processors.vt.assignment.request import (
            VisitTypeAssignmentRequestProcessor,
        )

        self.PROCESS_TYPE_TO_PROCESSOR = {
            ProcessType.PROCESS_BILL_REFUND_REQUEST.value: BillRefundProcessor,
            ProcessType.VISIT_TYPE_ASSIGNMENT.value: VisitTypeAssignmentRequestProcessor,
        }
        self.process_type = process_type

    def get_processor(self, process_type=None):
        process_type = self.process_type or process_type
        return self.PROCESS_TYPE_TO_PROCESSOR.get(process_type)
