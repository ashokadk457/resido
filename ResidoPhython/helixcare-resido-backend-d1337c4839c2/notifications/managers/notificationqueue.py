from rest_framework import status
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.managers.model.base import BaseModelManager
from helixauth.constants import NotificationChannel
from notifications.managers.template.registry import TemplateRegistry
from notifications.models import NotificationQueue
from notifications.utils import Utils, get_staff_communication_details


class NotificationQueueManager(BaseModelManager):
    model = NotificationQueue

    @classmethod
    def send_email_notification(
        cls, user, template_code, extra_body_inputs={}, extra_title_inputs={}, event="4"
    ):
        notif = cls.model()
        _, lang = Utils.check_notification_type_provider(user)
        notification_type = NotificationChannel.EMAIL.value
        email, _, _ = get_staff_communication_details(id=str(user.id))
        setting = Utils.get_tenant_notification(notification_type, event, lang)
        if not setting:
            raise StandardAPIException(
                code="missing_notification_setting",
                detail=ERROR_DETAILS["missing_notification_setting"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        template_registry = TemplateRegistry()
        template = template_registry.get_template(template_code=template_code)
        payload = {}
        payload["message"] = template["body"].format(**extra_body_inputs)
        payload["subject"] = template["title"].format(**extra_title_inputs)
        notif.notification_setting = setting
        notif.payload = payload
        notif.receiving_address = email
        notif.save()
