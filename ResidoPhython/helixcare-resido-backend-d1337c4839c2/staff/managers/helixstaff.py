from django.db.models import Manager
from django.db import connection
from common.managers.model.base import BaseModelManager
from common.utils.logging import logger
from helixauth.models import HelixUser, UserRole
from staff.models import HelixStaff


class HelixStaffManager(BaseModelManager, Manager):
    model = HelixStaff

    def __init__(self, *args, **kwargs):
        self.tenant_obj = kwargs.pop("tenant_obj", None)
        self.customer_admin_data = kwargs.pop("customer_admin_data", None)
        self.staff_obj = None
        self.user_obj = None

        super().__init__(*args, **kwargs)

    def get_provider(self, staff_id):
        return self.filter_by(id=staff_id).first()

    def create_customer_admin_user(self):
        """
        Creates the customer admin user account
        Returns: HelixUser instance
        """
        email = self.customer_admin_data.get("email")
        first_name = self.customer_admin_data.get("first_name")
        last_name = self.customer_admin_data.get("last_name")
        password = self.customer_admin_data.get("password")

        try:
            self.user_obj = HelixUser.objects.create_superuser(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            return self.user_obj
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise

    def create_customer_admin_staff(self):
        """
        Creates the HelixStaff record for customer admin
        """
        try:
            self.staff_obj = HelixStaff.objects.create(user=self.user_obj)

            role = UserRole.objects.filter(role_name="Site Administrator").first()
            if role:
                self.staff_obj.user_roles.set([role])
                self.staff_obj.save()

            return self.staff_obj
        except Exception as e:
            logger.error(f"Failed to create staff record: {str(e)}")
            raise

    def notify_customer_admin(self):
        """
        Sends welcome email to customer admin with credentials
        """
        from notifications.managers.notification import NotificationsManager
        from notifications.constants import TemplateCode
        from notifications.utils import Utils
        from notifications.managers.notificationqueue import NotificationQueueManager

        template_type = TemplateCode.EMAIL_CUSTOMER_ONBOARDING_SUCCESS.value
        tenant_domain = (
            getattr(connection, "tenant", self.tenant_obj).url
            if self.tenant_obj
            else ""
        )

        template_context = {
            "first_name": self.customer_admin_data.get("first_name"),
            "last_name": self.customer_admin_data.get("last_name"),
            "email": self.customer_admin_data.get("email"),
            "username": self.customer_admin_data.get("email"),
            "password": self.customer_admin_data.get("password"),
            "tenant_name": self.tenant_obj.name if self.tenant_obj else "",
            "login_url": f"https://{tenant_domain}",
        }

        try:
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
                receiving_address=template_context.get("email"),
            )

        except Exception as e:
            logger.error(f"Failed to queue welcome email: {str(e)}")
            raise

    def create_customer_admin_and_notify(self):
        """
        Main method to create customer admin and send welcome email
        Returns: HelixStaff instance
        """
        try:
            self.user_obj = self.create_customer_admin_user()
            self.staff_obj = self.create_customer_admin_staff()
            self.notify_customer_admin()
            logger.info("Customer admin creation & notification completed")
            return self.staff_obj
        except Exception as e:
            logger.error(f"Customer admin creation failed: {str(e)}")
            raise

    @classmethod
    def create_site_admin(cls, **kwargs):
        super_user = HelixUser.objects.create_superuser(
            username=kwargs.get("username"),
            email=kwargs.get("email"),
            password=kwargs.get("password"),
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            access_level=kwargs.get("access_level"),
        )
        staff = HelixStaff.objects.create(user=super_user)
        role = UserRole.objects.filter(role_name="Site Administrator").first()
        if role:
            staff.user_roles.set([role])
            staff.save()

        return {
            "id": str(staff.id),
            "user_id": str(super_user.id),
            "username": kwargs.get("username"),
            "email": kwargs.get("email"),
            "password": kwargs.get("password"),
            "first_name": kwargs.get("first_name"),
            "last_name": kwargs.get("last_name"),
        }
