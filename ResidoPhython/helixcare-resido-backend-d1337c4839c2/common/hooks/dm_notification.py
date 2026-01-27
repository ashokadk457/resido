"""
Data Migration Notification Hook

Triggered during POST_DM_HOOKS (Phase 2) to send a welcome notification
to the customer admin after data migration completes.
"""
from django.db import connection

from common.utils.logging import logger
from notifications.managers.notification import NotificationsManager
from notifications.managers.notificationqueue import NotificationQueueManager
from notifications.utils import Utils
from notifications.constants import TemplateCode


class CustomerDMNotificationManager:
    """
    Sends welcome email with login credentials after data migration completes.
    """

    def __init__(self, **kwargs):
        self.tenant_obj = kwargs.get("tenant_obj")
        self.customer_admin_data = kwargs.get("customer_admin_data", {})

    def notify_customer_admin(self):
        """
        Sends welcome email with login credentials to customer admin
        using async NotificationQueue.
        """
        email = self.customer_admin_data.get("email")
        if not email:
            logger.info("No admin email provided, skipping notification")
            return

        try:
            template_type = TemplateCode.EMAIL_CUSTOMER_ONBOARDING_SUCCESS.value

            tenant_domain = (
                connection.tenant.url
                if hasattr(connection, "tenant")
                else self.tenant_obj.url
            )

            template_context = {
                "first_name": self.customer_admin_data.get("first_name"),
                "last_name": self.customer_admin_data.get("last_name"),
                "email": email,
                "username": email,
                "password": self.customer_admin_data.get("password"),
                "tenant_name": self.tenant_obj.name if self.tenant_obj else "",
                "login_url": f"https://{tenant_domain}",
            }

            email_setting = Utils.get_tenant_notification("EMAIL", "4", "EN")
            if not email_setting:
                raise Exception("Email notification setting not found")

            template_content = NotificationsManager._load_template(template_type)
            html_content = NotificationsManager._render_template(
                template_content, template_context
            )
            subject = NotificationsManager._get_subject_for_template(template_type)

            nq_manager = NotificationQueueManager()
            nq_manager.create_object(
                notification_setting=email_setting,
                user=None,
                provider=None,
                payload={
                    "subject": subject,
                    "message": html_content,
                    "html_message": html_content,
                },
                receiving_address=email,
            )

            logger.info("Welcome email queued for %s", email)

        except Exception:
            logger.exception("Failed to queue welcome email")
            raise

    @classmethod
    def run(cls, **kwargs):
        """
        Entry point called from Tenant Post DM Hooks.
        """
        if not kwargs.get("customer_admin_data"):
            logger.info("No admin data provided, hook skipped")
            return None

        try:
            obj = cls(**kwargs)
            obj.notify_customer_admin()
        except Exception:
            logger.exception("Hook execution failed")
            raise
