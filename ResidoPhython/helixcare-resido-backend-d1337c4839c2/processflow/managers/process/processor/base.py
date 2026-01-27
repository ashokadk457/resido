import uuid

from celery import shared_task
from django.db import transaction

from common.exception import StandardExceptionHandler
from common.response import StandardAPIResponse
from common.utils.logging import logger, set_request_id


class BaseAsyncTaskProcessor:
    def __init__(self, process_id=None, request_id=None, process_type=None, **kwargs):
        self.process_id = process_id
        self.process_type = process_type
        self.request_id = request_id
        self.kwargs = kwargs or {}
        self.kwargs["process_id"] = self.process_id
        self.kwargs["request_id"] = self.request_id
        self.kwargs["process_type"] = self.process_type

    @classmethod
    def set_request_id_from_task(cls, request_id):
        set_request_id(request_id=request_id)

    @classmethod
    def unset_request_id_from_task(cls):
        set_request_id(request_id=uuid.uuid4())

    @classmethod
    def unpack_task_details(cls, **kwargs):
        process_id = kwargs.get("process_id", None)
        task_id = kwargs.get("task_id", process_id)
        request_id = kwargs.get("request_id", uuid.uuid4())
        process_type = kwargs.get("process_type")
        object_name = kwargs.get("object_name", None)
        # cls.set_request_id_from_task(request_id=request_id)

        return task_id, process_type, process_id, object_name, request_id, kwargs

    @staticmethod
    @shared_task
    def process(**kwargs):
        """
            Main method that receives the celery task
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def _run(cls, **kwargs):
        """
            Main method that runs the business logic of the task processing. Called by _process()
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    @classmethod
    def _process(cls, **kwargs):
        from processflow.managers.process.core import ProcessManager

        (
            task_id,
            process_type,
            process_id,
            object_name,
            request_id,
            kwargs,
        ) = cls.unpack_task_details(**kwargs)
        cls.set_request_id_from_task(request_id=request_id)
        logger.info(
            msg=f"Received message with process_type {process_type} for process_id {process_id} - {kwargs}",
            extra={"task_id": task_id},
        )

        pm = ProcessManager.init(process_id=process_id)
        pm.update_process_status_from_processing_status(processing_status=None)
        status, error_body, error_code = cls._run(**kwargs)
        pm.update_process_status_from_processing_status(
            processing_status=status, error_code=error_code, error_body=error_body
        )

        logger.info(
            msg=f"Completed Task processing with id - {task_id} - {process_type} with status {status} and error {error_body}",
            extra={"task_id": task_id},
        )

        cls._commit()
        cls.unset_request_id_from_task()
        return status, error_body

    def enqueue_adhoc_process(self):
        """

            Main method that enqueues the async task in the task queue.
            Called by the Sync code to enqueue a background async task.
            Must return an async task id

        :return:
        """
        async_task = self.process.apply_async(
            kwargs=self.kwargs, task_id=self.process_id, countdown=3
        )
        return str(async_task.id)

    @classmethod
    def _commit(cls):
        logger.info("Making extra commit")
        try:
            transaction.commit()
        except Exception as e:
            logger.info(f"Exception occurred while committing transaction - {str(e)}")

    @classmethod
    def _process_exception(cls, exception):
        handled_exception_response = StandardExceptionHandler.handle(
            exc=exception, response=StandardAPIResponse(status=400)
        )
        if not isinstance(handled_exception_response, StandardAPIResponse):
            error_data = str(handled_exception_response)
            return StandardAPIResponse(
                data={"code": error_data, "message": error_data}
            ).data

        return handled_exception_response.data
