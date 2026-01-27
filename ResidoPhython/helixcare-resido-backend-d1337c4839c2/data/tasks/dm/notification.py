from dm.tasks.dm.base import BaseDataMigrationTask
from notifications.managers.setting import NotificationSettingsManager


class NotificationSettingMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(NotificationSettingMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        NotificationSettingsManager.seed_notification_settings()
