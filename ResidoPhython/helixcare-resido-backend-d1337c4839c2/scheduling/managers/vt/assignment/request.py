from customer_backend.managers.tenant import TenantManager
from processflow.constants import ProcessType
from processflow.managers.process.core import ProcessManager
from scheduling.constants import VisitTypeAssignmentRequestStatus


class VisitTypeAssignmentRequestManager:
    def __init__(self, **kwargs):
        self.tenant_id = (
            kwargs.get("tenant_id")
            if kwargs.get("tenant_id")
            else str(TenantManager().tenant_id)
        )
        self.assignment_request_obj = kwargs.get("assignment_request_obj")
        self.assignment_request_id = (
            str(self.assignment_request_obj.id)
            if self.assignment_request_obj is not None
            else kwargs.get("assignment_request_id")
        )

    def _init_async_process(self, process_type):
        pm = ProcessManager(process_type=process_type)
        kwargs = {
            "tenant_id": self.tenant_id,
            "assignment_request_id": self.assignment_request_id,
        }
        object_name = self.assignment_request_obj.display_id
        return pm.init_and_enqueue_adhoc_aysnc_process(
            object_id=self.assignment_request_id, object_name=object_name, **kwargs
        )

    def init_adhoc_vt_assignment_process(self):
        return self._init_async_process(
            process_type=ProcessType.VISIT_TYPE_ASSIGNMENT.value
        )

    def _update_request_status(self, status):
        """
        Updates the status of the assignment request and saves it.

        This method changes the `status` field of the associated
        assignment request object and persistently saves the changes.
        It returns the updated assignment request object after
        performing the operation.

        :param status: The new status value to be set for the assignment
                       request.
        :type status: Any
        :return: The updated assignment request object.
        :rtype: AssignmentRequest
        """
        self.assignment_request_obj.status = status
        self.assignment_request_obj.save()
        return self.assignment_request_obj

    def mark_request_as_in_progress(self):
        """
        Updates the status of a visit type assignment request to 'IN_PROGRESS'.
        This method modifies the request status to indicate that processing has
        begun on the current visit type assignment.

        :return: The result of the status update operation.
        :rtype: AssignmentRequest
        """
        return self._update_request_status(
            status=VisitTypeAssignmentRequestStatus.IN_PROGRESS.value
        )

    def mark_request_as_completed(self):
        """
        Updates the status of a request to mark it as completed.

        This method modifies the status of a visit type assignment request to indicate
        that it has been completed. Internally, it delegates the update to the
        `_update_request_status` method by providing the appropriate status value.

        :return: The result of the status update operation.
        :rtype: AssignmentRequest
        """
        return self._update_request_status(
            status=VisitTypeAssignmentRequestStatus.COMPLETED.value
        )

    def mark_request_as_failed(self):
        """
        Marks the request as failed by updating its status to FAILED.

        This method updates the status of a visit type assignment request to FAILED
        using the `_update_request_status` method. It is used to signify that the
        request could not be completed successfully.

        :return: The result of the status update operation.
        :rtype: AssignmentRequest
        """
        return self._update_request_status(
            status=VisitTypeAssignmentRequestStatus.FAILED.value
        )

    def update_request_status_from_processing_status(self, processing_status):
        """
        Updates the request status based on the provided processing status.

        This method evaluates the given `processing_status` parameter and updates
        the status of the request accordingly. If no processing status is provided
        (None), the request is marked as 'in_progress'. If the processing status is
        False, the request is marked as 'failed'. For any other truthy value, the
        request is marked as 'completed'.

        :param processing_status: Indicates the processing status of the request.
                                  It can be None, False, or any truthy value.
        :type processing_status: Optional[bool]
        :return: The result of the corresponding mark request operation, determined
                 by the evaluation of the given processing status.
        """
        if processing_status is None:
            return self.mark_request_as_in_progress()

        if processing_status is False:
            return self.mark_request_as_failed()

        return self.mark_request_as_completed()
