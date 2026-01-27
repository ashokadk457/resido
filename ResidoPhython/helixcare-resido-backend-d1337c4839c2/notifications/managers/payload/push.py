from notifications.managers.template.registry import TemplateRegistry


class PushNotificationPayloadBuilder:
    def __init__(
        self,
        notification_type,
        platform,
        device_token,
        template_code,
        extra_data=None,
        template_body_params=None,
    ):
        self.notification_type = notification_type
        self.platform = platform
        self.device_token = device_token
        self.extra_data = extra_data
        self.template_code = template_code
        self.template_body_params = template_body_params
        self.template_registry = TemplateRegistry()
        self.template = self.template_registry.get_template(
            template_code=self.template_code
        )
        self.payload = {}

    def build(self, reset=True):
        if not reset and self.payload:
            return self.payload

        return self._build()

    def _build(self):
        self.template["body"] = self.template["body"].format(
            **self.template_body_params
        )
        self.payload = {
            "platform": self.platform,
            "device_token": self.device_token,
            **self.template,
            "data": self.extra_data,
        }
        return self.payload
