import uuid
from datetime import datetime, timedelta

from log_request_id import local

from common.constants import UTC_TIMEZONE
from common.utils.logging import logger
from processflow.constants import (
    ProcessStatus,
    RUNNING_PROCESS_TIME_THRESHOLD_IN_MINUTES,
    LONG_RUNNING_PROCESS_ERROR_BODY,
    ProcessTriggerType,
)
from processflow.models import Process
from processflow.managers.process.processor.factory import ProcessorFactory


class ProcessManager:
    @classmethod
    def init(cls, process_id):
        if not process_id:
            return None

        process_obj = Process.objects.filter(id=process_id).first()
        if not process_obj:
            return None

        return cls(process_obj=process_obj, process_type=process_obj.process_type)

    def __init__(self, process_id=None, process_obj=None, process_type=None):
        self.process_type = process_type
        self.process_obj = process_obj
        self.process_id = (
            process_id if self.process_obj is None else str(self.process_obj.id)
        )
        self.processor_factory = ProcessorFactory(process_type=process_type)

    def create_process(
        self,
        request_id,
        object_id,
        object_name,
        periodic_task_id=None,
        raw_payload=None,
        task_id=None,
        trigger_type=None,
        status=ProcessStatus.QUEUED.value,
    ):
        self.process_obj = Process.objects.create(
            periodic_task_id=periodic_task_id,
            request_id=request_id,
            object_id=object_id,
            object_name=object_name,
            process_type=self.process_type,
            raw_payload=raw_payload,
            task_id=task_id,
            trigger_type=trigger_type,
            status=status,
        )
        self.process_id = str(self.process_obj.id)
        return self.process_obj

    def init_and_enqueue_adhoc_aysnc_process(self, object_id, object_name, **kwargs):
        request_id = getattr(local, "request_id", uuid.uuid4())
        self.process_obj = self.create_process(
            trigger_type=ProcessTriggerType.ADHOC_VIA_API.value,
            request_id=request_id,
            object_id=object_id,
            object_name=object_name,
        )

        processor_class = self.processor_factory.get_processor()
        processor = processor_class(
            request_id=request_id,
            process_id=self.process_id,
            process_type=self.process_type,
            **kwargs,
        )
        task_id = processor.enqueue_adhoc_process()
        self.process_obj.set_task_id(task_id=task_id)

        return self.process_id

    def _update_process_status(
        self, process_status, error_body=None, error_code=None, report=None
    ):
        logger.info(
            f"Updating process status for process with task_id {self.process_obj.task_id} as {process_status}"
            f" with error_body: {error_body} and error_code: {error_code}"
        )
        try:
            return self.process_obj.update_status(
                new_status=process_status,
                error_body=error_body,
                error_code=error_code,
                report=report,
            )
        except Exception as e:
            logger.info(
                f"Exception occurred while updating the process status for process_id {self.process_id} "
                f"with new status {process_status}: {str(e)}"
            )
            raise e

    def mark_process_as_running(self):
        return self._update_process_status(process_status=ProcessStatus.RUNNING.value)

    def mark_process_as_completed(self, report=None, error_body=None, error_code=None):
        return self._update_process_status(
            process_status=ProcessStatus.COMPLETED.value,
            report=report,
            error_body=error_body,
            error_code=error_code,
        )

    def mark_process_as_failed(self, error_body=None, error_code=None):
        return self._update_process_status(
            process_status=ProcessStatus.FAILED.value,
            error_body=error_body,
            error_code=error_code,
        )

    def update_process_status_from_processing_status(
        self, processing_status, error_code=None, error_body=None
    ):
        """
        Updates the process status based on the provided processing status. This method
        determines the current state of a process by evaluating the input processing status.
        It transitions the process to one of the three states: running, failed, or completed,
        depending on the value of the processing_status parameter. If the process is marked
        as failed, additional error information can be specified using error_code and
        error_body.

        :param processing_status: The current status of the processing to evaluate.
            It can be None for a running state, False for a failed state, or any other
            value for a completed state.
        :param error_code: Optional error code to be used when marking the process as
            failed.
        :param error_body: Optional detailed error information associated with the
            failed state.
        :return: The result of transitioning the process into one of the corresponding
            states: running, failed, or completed.
        """
        if processing_status is None:
            return self.mark_process_as_running()

        if processing_status is False:
            return self.mark_process_as_failed(
                error_code=error_code, error_body=error_body
            )

        return self.mark_process_as_completed()

    @classmethod
    def mark_long_running_processes_as_failed(cls):
        curr_time = datetime.now(tz=UTC_TIMEZONE)
        time_in_past = curr_time - timedelta(
            minutes=RUNNING_PROCESS_TIME_THRESHOLD_IN_MINUTES
        )
        all_running_processes = Process.objects.filter(
            status=ProcessStatus.RUNNING.value, updated_at__lte=time_in_past
        )
        logger.info(
            f"Marking long running processes as failed. Total such processes: {len(all_running_processes)}"
        )
        for long_running_process in all_running_processes:
            pm = cls.init(process_id=str(long_running_process.id))
            pm.mark_process_as_failed(
                error_code=400, error_body=LONG_RUNNING_PROCESS_ERROR_BODY
            )

        return len(all_running_processes)
