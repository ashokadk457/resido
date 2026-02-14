"""
Customer Onboarding Hook

Triggered during POST_LAUNCH_HOOKS (Phase 1) to create customer
records and admin user accounts.
"""
import copy

from common.utils.logging import logger
from locations.models import Customer
from staff.managers.helixstaff import HelixStaffManager


class CustomerOnboardingManager:
    """
    Creates customer admin staff during tenant launch.

    Runs during Phase 1 (POST_LAUNCH_HOOKS) after tenant infrastructure
    is created but before data migration.
    """

    def __init__(self, **kwargs):
        self.tenant_obj = kwargs.get("tenant_obj")
        self.customer_data = copy.deepcopy(kwargs.get("customer_data", {}))
        self.customer_admin_data = copy.deepcopy(kwargs.get("customer_admin_data", {}))

        self.customer_obj = None
        self.customer_admin_obj = None

    def create_customer(self):
        """
        Creates the Customer object.
        """
        if not self.customer_data:
            return None

        name = self.customer_data.get("name")
        email = self.customer_data.get("email")

        if not name or not email:
            logger.error("Customer name and email are required")
            return None

        try:
            self.customer_obj = Customer.objects.create(
                name=name,
                email=email,
                short_name=self.customer_data.get("short_name"),
                customer_url=self.customer_data.get("customer_url"),
                brand_color=self.customer_data.get("brand_color", "#3B1550"),
            )

            logger.info("Customer created (id=%s)", self.customer_obj.id)
            return self.customer_obj

        except Exception:
            logger.exception("Failed to create customer")
            raise

    def create_customer_admin(self):
        """
        Creates the customer admin user WITHOUT sending email.
        """
        if not self.customer_admin_data:
            return None

        try:
            staff_manager = HelixStaffManager(
                tenant_obj=self.tenant_obj,
                customer_admin_data=self.customer_admin_data,
            )

            staff_manager.create_customer_admin_user()
            self.customer_admin_obj = staff_manager.create_customer_admin_staff()

            if self.customer_obj:
                self.customer_admin_obj.customers.add(self.customer_obj)

            logger.info("Customer admin created (id=%s)", self.customer_admin_obj.id)
            return self.customer_admin_obj

        except Exception:
            logger.exception("Failed to create customer admin")
            raise

    def onboard(self):
        """
        Main onboarding method.
        """
        try:
            self.create_customer()
            self.create_customer_admin()

            logger.info("Customer onboarding completed")
            return self.customer_admin_obj

        except Exception:
            logger.exception("Customer onboarding failed")
            raise

    @classmethod
    def run(cls, **kwargs):
        """
        Entry point called from Tenant Post Launch Hooks.
        """
        if not kwargs.get("customer_admin_data"):
            return None

        try:
            obj = cls(**kwargs)
            return obj.onboard()
        except Exception:
            logger.exception("Customer onboarding hook execution failed")
            raise
