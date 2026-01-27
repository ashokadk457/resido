import json
import traceback
import uuid

from django_celery_beat.models import CrontabSchedule, PeriodicTask

from common.constants import PERIODIC_TASKS_JSON_FILE_PATH
from common.utils.logging import logger, get_request_id, set_request_id
from processflow.constants import ProcessStatus, ProcessTriggerType
from processflow.managers.process.core import ProcessManager


class AsyncPeriodicTaskManager:
    def __init__(self, **kwargs):
        self.original_kwargs = kwargs
        self.periodic_task_id = kwargs.get("periodic_task_id")
        self.task_id = kwargs.get("task_id")
        self.request_id = kwargs.get("request_id")
        self.process_trigger_type = kwargs.get(
            "process_trigger_type", ProcessTriggerType.PERIODIC.value
        )
        self.process_manager = ProcessManager(process_type=kwargs.get("process_type"))
        self.report = None
        self.error_body = None

    def init_process(self):
        self.request_id = get_request_id()
        if self.task_id is None:
            self.task_id = self.request_id
        self.process_manager.create_process(
            trigger_type=self.process_trigger_type,
            request_id=self.request_id,
            task_id=self.task_id,
            object_id=None,
            object_name=None,
            periodic_task_id=self.periodic_task_id,
            status=ProcessStatus.RUNNING.value,
        )

    def mark_process_as_completed(self):
        self.process_manager.mark_process_as_completed(
            report=self.report, error_body=self.error_body
        )

    def _run(self):
        raise NotImplementedError()

    def run(self):
        set_request_id(request_id=self.request_id or str(uuid.uuid4()))
        self.init_process()
        try:
            status = self._run()
        except Exception as e:
            logger.info(f"Exception occurred while executing periodic task: {str(e)}")
            traceback.print_exc()
            self.process_manager.mark_process_as_failed(error_body=str(e))
        else:
            if status:
                self.mark_process_as_completed()
            else:
                self.process_manager.mark_process_as_failed(error_body=self.error_body)
        set_request_id(request_id=str(uuid.uuid4()))

    @classmethod
    def seed_tenant_tasks(cls):
        # Lazy import to avoid circular dependency
        from customer_backend.managers.tenant import TenantManager

        tm = TenantManager()
        logger.info("Loading all tenant tasks...")
        with open(PERIODIC_TASKS_JSON_FILE_PATH) as json_file:
            all_tasks = json.loads(json_file.read())

        for task in all_tasks:
            crontab = task["crontab"]
            cron_items = crontab.split(" ")
            crontab_obj, _ = CrontabSchedule.objects.get_or_create(
                minute=cron_items[0],
                hour=cron_items[1],
                day_of_month=cron_items[2],
                month_of_year=cron_items[3],
                day_of_week=cron_items[4],
            )
            task["crontab"] = crontab_obj

            kwargs = task["kwargs"]
            kwargs["tenant_id"] = tm.tenant_id_str
            kwargs["schema"] = tm.tenant_schema_name
            task["kwargs"] = json.dumps(kwargs)
            task["name"] = f"{task['name']} - {tm.tenant_schema_name}"
            task_obj, _ = PeriodicTask.objects.update_or_create(
                name=task["name"], defaults=task
            )
            kwargs["periodic_task_id"] = task_obj.id
            _kwargs = json.dumps(kwargs)
            task_obj.kwargs = _kwargs
            task_obj.save()

        logger.info("Loaded all tenant tasks...")
