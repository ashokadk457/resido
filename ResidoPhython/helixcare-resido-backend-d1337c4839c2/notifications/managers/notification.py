import os
import re

from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context

from notifications.utils import (
    Utils,
    get_resident_communication_details,
    get_staff_communication_details,
)
from notifications.managers.notificationqueue import NotificationQueueManager
from common.utils.logging import logger


class NotificationsManager:
    def __init__(self, user=None, event_type="4"):
        self.user = user
        self.event_type = event_type  # Must be assigned before use
        if self.user:
            self.is_resident = self.user.__class__.__name__ == "Resident"
            if self.is_resident:
                self.mode, self.lang = Utils.check_notification_type(self.user)
            else:
                self.mode, self.lang = Utils.check_notification_type_provider(self.user)
            self.sms_setting = Utils.get_tenant_notification(
                "SMS", self.event_type, self.lang
            )
            self.email_setting = Utils.get_tenant_notification(
                "EMAIL", self.event_type, self.lang
            )

    @staticmethod
    def build_message(template, variables):
        return template.format(**variables)

    @staticmethod
    def get_comm_details(user):
        if user.__class__.__name__ == "Resident":
            return get_resident_communication_details(id=user.id)
        else:
            return get_staff_communication_details(id=user.id)

    def send_sms(self, text_message):
        nq_manager = NotificationQueueManager()
        payload = {}
        payload["message"] = text_message
        _, phone_number, country_code = self.get_comm_details(user=self.user)
        receiving_address = f"{country_code}{phone_number}"
        return nq_manager.create_object(
            notification_setting=self.sms_setting,
            user=self.user if self.is_resident else None,
            provider=self.user if not self.is_resident else None,
            payload=payload,
            receiving_address=receiving_address,
        )

    def _store_email_in_connecthub(self, subject, body, email):
        data = {
            "subject": subject,
            "body": body,
            "is_draft": False,
            "recipients": [
                {
                    "content_type": (
                        47 if self.user.__class__.__name__ == "Patient" else ""
                    ),
                    "object_id": str(self.user.id),
                    "recipient_type": "to",
                    "email_address": email,
                }
            ],
            "attachments": [],
        }
        # to avoid circular import error
        from connecthub.serializers import CreateEmailSerializer

        srz = CreateEmailSerializer(data=data, context={"no_email_sending": True})
        if srz.is_valid(raise_exception=False):
            srz.save()

    def send_email(self, subject, body, store_email_in_connecthub=False):
        nq_manager = NotificationQueueManager()
        payload = {}
        payload["subject"] = subject
        payload["message"] = body

        # Check if body contains HTML and add it to payload
        is_html = bool(re.search(r"<[^>]+>", body))
        if is_html:
            payload["html_message"] = body

        email, _, _ = self.get_comm_details(user=self.user)

        if store_email_in_connecthub:
            self._store_email_in_connecthub(subject=subject, body=body, email=email)
        return nq_manager.create_object(
            notification_setting=self.email_setting,
            user=self.user if self.is_resident else None,
            provider=self.user if not self.is_resident else None,
            payload=payload,
            receiving_address=email,
        )

    @staticmethod
    def _load_template(template_code):
        """
        Loads HTML email template from notifications/templates/html/ directory

        Args:
            template_code: Template filename without extension (e.g., 'email_customer_onboarding_success')

        Returns:
            Template content as string
        """
        template_path = os.path.join(
            settings.BASE_DIR,
            "notifications",
            "templates",
            "html",
            f"{template_code}.html",
        )

        try:
            with open(template_path, "r", encoding="utf-8") as template_file:
                return template_file.read()
        except FileNotFoundError:
            logger.error(f"Email template not found: {template_path}")
            raise

    @staticmethod
    def _render_template(template_content, context):
        """
        Renders template with context variables

        Args:
            template_content: HTML template string
            context: Dict of template variables

        Returns:
            Rendered HTML string
        """
        template = Template(template_content)
        django_context = Context(context)
        return template.render(django_context)

    @staticmethod
    def _get_subject_for_template(template_code):
        """
        Returns email subject for template code

        Args:
            template_code: Template identifier

        Returns:
            Email subject string
        """
        subjects = {
            "email_customer_onboarding_success": "Welcome to RESIDO - Your Account is Ready!",
            "email_customer_dm_success": "Your RESIDO Account Setup is Complete",
            "email_property_created": "New Property Created in RESIDO",
            "email_location_created": "New Location Created in RESIDO",
        }
        return subjects.get(template_code, "RESIDO Notification")

    @classmethod
    def send_email_in_sync(cls, template_code, emails, template_context=None):
        """
        Sends email synchronously using HTML template


        Args:
            template_code: Template identifier (e.g., 'email_customer_onboarding_success')
            emails: List of recipient email addresses
            template_context: Dictionary of variables for template rendering

        Example:
            NotificationsManager.send_email_in_sync(
                template_code='email_customer_onboarding_success',
                emails=['admin@example.com'],
                template_context={
                    'first_name': 'John',
                    'username': 'john@example.com',
                    'password': 'temp123',
                    'login_url': 'https://tenant.resido.com'
                }
            )
        """

        try:
            # Load HTML template
            template_content = cls._load_template(template_code)

            # Render template with context
            html_content = cls._render_template(
                template_content, template_context or {}
            )

            # Get email subject
            subject = cls._get_subject_for_template(template_code)

            send_mail(
                subject=subject,
                message="",  # Plain text version (empty for HTML-only emails)
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False,
            )

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise
