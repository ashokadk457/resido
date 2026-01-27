from notifications.apiviews import sendEmail
from notifications.constants import TemplateCode
from notifications.managers.template.registry import TemplateRegistry
from scheduling.constants import EventTrigger


class MeetingEmailNotificationDispatcher:
    def send(self, **kwargs):
        trigger = kwargs.get("trigger")
        if trigger == EventTrigger.INVITE.value:
            return self.send_invite_email(**kwargs)

    @staticmethod
    def get_template_code(**kwargs):
        if "event" in kwargs:
            return TemplateCode.SCHEDULED_FACEMEET_INVITE.value

        return TemplateCode.QUICK_JOIN_FACEMEET_INVITE.value

    def get_invite_email_body_payload(self, **kwargs):
        template_registry = TemplateRegistry()
        template_code = self.get_template_code(**kwargs)
        template = template_registry.get_template(template_code=template_code)
        subject = template["title"].format(title=kwargs.get("event", {}).get("title"))
        body = template["body"].format(
            _name=kwargs.get("name"),
            host_name=kwargs.get("host_name"),
            title=kwargs.get("event", {}).get("title"),
            start_date=kwargs.get("event", {}).get("start_date"),
            start_time=kwargs.get("event", {}).get("start_time"),
            end_time=kwargs.get("event", {}).get("end_time"),
            meeting_room=kwargs.get("meeting_room"),
            meeting_link=kwargs.get("meeting_link"),
        )
        return subject, body

    def send_invite_email(self, **kwargs):
        subject, body = self.get_invite_email_body_payload(**kwargs)
        sendEmail(
            subject=subject,
            message=body,
            emails=[kwargs.get("email")],
            sender_id=None,
            rec_id=None,
        )
