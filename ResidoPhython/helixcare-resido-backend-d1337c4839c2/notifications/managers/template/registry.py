import os

from django.conf import settings
from django.db import connection
from django.template import Template, Context

from common.utils.logging import logger
from meetings.constants import (
    FACEMEET_EMAIL_INVITE_TITLE,
    QUICK_JOIN_FACEMEET_INVITE_BODY,
    SCHEDULED_FACEMEET_EMAIL_INVITE_BODY,
    QUICK_JOIN_FACEMEET_INVITE_TITLE,
)
from notifications.constants import TemplateCode


class TemplateRegistry:
    REGISTRY = {
        TemplateCode.QUICK_JOIN_FACEMEET_INVITE.value: {
            "title": QUICK_JOIN_FACEMEET_INVITE_TITLE,
            "body": QUICK_JOIN_FACEMEET_INVITE_BODY,
        },
        TemplateCode.SCHEDULED_FACEMEET_INVITE.value: {
            "title": FACEMEET_EMAIL_INVITE_TITLE,
            "body": SCHEDULED_FACEMEET_EMAIL_INVITE_BODY,
        },
        TemplateCode.INCOMING_CALL.value: {
            "title": "Incoming Call",
            "body": "{_name} is inviting you to join the call",
        },
        TemplateCode.MEETING_STARTED.value: {
            "title": "Meeting Started",
            "body": "{_name} has started the meeting.",
        },
        TemplateCode.ACCOUNT_ACTIVATE_NOTIFICATION.value: {
            "title": "Account Activated",
            "body": "Your account has been activated.",
        },
        TemplateCode.ACCOUNT_UNLOCK_NOTIFICATION.value: {
            "title": "Account Unlocked",
            "body": "Your account has been unlocked.",
        },
        TemplateCode.OTP_VERIFICATION.value: {
            "title": "OTP Verification",
            "body": "Your OTP is: {otp}",
        },
        TemplateCode.FORGOT_PASSWORD.value: {
            "title": "Reset Your Password",
            "body": "Your password reset OTP is: {otp}",
        },
        TemplateCode.USER_ACCOUNT_CREATION.value: {
            "title": "Welcome to Resido",
            "body": "Your account has been created. Your OTP is: {otp}",
        },
        TemplateCode.EMAIL_PROPERTY_CREATED.value: {
            "title": "New Property Created",
            "body": "A new property '{property_name}' has been created.",
        },
        TemplateCode.EMAIL_LOCATION_CREATED.value: {
            "title": "New Location Created",
            "body": "A new location '{location_name}' has been created.",
        },
    }

    HTML_TEMPLATES = {
        TemplateCode.OTP_VERIFICATION.value: "otp_verification.html",
        TemplateCode.FORGOT_PASSWORD.value: "forgot_password.html",
        TemplateCode.USER_ACCOUNT_CREATION.value: "user_account_creation.html",
        TemplateCode.EMAIL_PROPERTY_CREATED.value: "email_property_created.html",
        TemplateCode.EMAIL_LOCATION_CREATED.value: "email_location_created.html",
    }

    DEFAULT_NOTIFICATION = {
        "title": "New Notification from",
        "body": "New Notification from {_name}",
    }

    @classmethod
    def get_template(cls, template_code):
        return cls.REGISTRY.get(template_code, cls.DEFAULT_NOTIFICATION)

    @classmethod
    def get_html_template(cls, template_code, context):
        """Get HTML template content"""
        template_file = cls.HTML_TEMPLATES.get(template_code)
        logger.info(
            f"get_html_template: template_file={template_file}, template_code={template_code}"
        )
        if not template_file:
            return None, None

        try:
            domain = connection.tenant.domain
            domain = f"https://{domain}"
            absolute_static_url = f"{domain.rstrip('/')}{settings.STATIC_URL}"
            context["STATIC_URL"] = absolute_static_url
            logger.info(f"domain check: {absolute_static_url}")

            template_dir = os.path.join(
                settings.BASE_DIR, "notifications", "templates", "email"
            )
            template_path = os.path.join(template_dir, template_file)

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            template = Template(template_content)
            html_content = template.render(Context(context))
            subject = context.get("email_subject", cls.DEFAULT_NOTIFICATION["title"])
            return subject, html_content
        except Exception as e:
            logger.error(f"Error loading HTML template: {e}")
            return None, None

    @classmethod
    def get_email_content(cls, template_code, context=None, is_html=False):
        logger.info(
            f"get_email_content: template_code={template_code}, context={context}"
        )
        if context or is_html:
            # Try HTML template first
            subject, html_body = cls.get_html_template(template_code, context)
            if subject and html_body:
                return subject, html_body

        # Fallback to text template
        text_template = cls.get_template(template_code)
        subject = text_template["title"]
        body = text_template["body"]

        if context:
            try:
                subject = subject.format(**context)
                body = body.format(**context)
            except Exception:
                pass

        return subject, body

    @classmethod
    def is_html_template_used(cls, template_code):
        return template_code in cls.HTML_TEMPLATES
