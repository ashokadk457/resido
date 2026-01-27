from notifications.models import NotificationSetting


class NotificationSettingsManager:
    @classmethod
    def seed_notification_settings(cls):
        NotificationSetting.objects.update_or_create(
            notification_type="EMAIL", language="EN", event_type="4"
        )
        NotificationSetting.objects.update_or_create(
            notification_type="SMS",
            language="EN",
            event_type="4",
            message='{"validate_number": false}',
        )
