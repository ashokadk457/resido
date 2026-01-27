from common.utils.logging import logger
from notifications.helix_notification_sender import HelixNotificationSender
from notifications.models import NotificationQueue
from notifications.email_notification import EmailNotification
from notifications.voice_notification import VoiceNotification
from notifications.sms_notification import SMSNotification
from datetime import datetime


class HelixNotificationHandler:
    def checkShouldSend(self, entry):
        setting = entry.notification_setting
        if setting.when == "1":
            logger.info("Should send")
            return True
        now = datetime.now()
        current_hour = now.strftime("%H:%M:%S").split(":")[0]
        time_list = setting.send_time
        for t in time_list:
            t = t.split("-")
            if current_hour < int(t[1]) and current_hour > int(t[0]):
                return True
        return False

    def consume(self):
        qEntry = NotificationQueue.objects.filter(status=3).order_by("priority")
        logger.info(f"Picking notifications for delivery: {qEntry}")
        for entry in qEntry:
            logger.info(
                f"Sending {entry.notification_setting.notification_type} to {entry.receiving_address}; "
                f"notification_id {entry.id}"
            )
            if self.checkShouldSend(entry):
                if entry.notification_setting.notification_type == "EMAIL":
                    HelixNotificationSender().sender(EmailNotification(), entry)
                if entry.notification_setting.notification_type == "SMS":
                    HelixNotificationSender().sender(SMSNotification(), entry)
                if entry.notification_setting.notification_type == "CALL":
                    HelixNotificationSender().sender(VoiceNotification(), entry)
