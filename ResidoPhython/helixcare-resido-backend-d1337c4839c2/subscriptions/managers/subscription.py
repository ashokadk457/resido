from customer_backend.managers.tenant import TenantManager

from hb_core.utils.logging import logger

from common.models import HealthCareCustomerConfig
from subscriptions.managers.plan import PlanManager
from subscriptions.models.subscription import TenantSubscription


class TenantSubscriptionManager:
    @classmethod
    def run(cls, **kwargs):
        tenant_obj = kwargs.get("tenant_obj")
        if tenant_obj is None:
            tm = TenantManager()
            tenant_obj = tm.tenant_obj
        kwargs["tenant_obj"] = tenant_obj
        cls.create_tenant_config_based_on_subscription(**kwargs)
        return None

    @classmethod
    def create_tenant_config_based_on_subscription(cls, **kwargs):
        tenant_obj = kwargs.get("tenant_obj")
        (
            module_composition,
            settings,
        ) = cls.get_tenant_plan_module_composition_and_settings(tenant_obj=tenant_obj)
        if not module_composition:
            logger.warning(
                "No module composition found for tenant plan. Skipping seeding tenant config."
            )
            return None
        tenant_config_data = cls.upsert_tenant_config(
            tenant_obj=tenant_obj,
            module_composition=module_composition,
            settings=settings,
        )
        # RESIDO: No external service subscriptions needed
        return tenant_config_data

    @classmethod
    def create_subs_record_for_backward_compatibility(cls, tenant_obj, plan_obj):
        try:
            subscription_obj = TenantSubscription.objects.create(
                tenant=tenant_obj, plan=plan_obj
            )
        except Exception as e:
            logger.error(
                f"Subscription record creation failed due to an exception: {e}"
            )
            return None
        return subscription_obj

    @classmethod
    def get_tenant_plan_module_composition_and_settings(cls, tenant_obj):
        plan_code = tenant_obj.plan_code
        settings = tenant_obj.plan_settings

        # Look up Plan by code instead of name to avoid mismatch between
        # GENIUS default plan_name="Internal" and RESIDO plan names like "RESIDO Standard Plan"
        if not plan_code:
            logger.warning(
                f"No plan_code set for tenant {tenant_obj.schema_name}. Skipping tenant config seeding."
            )
            return None, settings

        from subscriptions.models.plan import Plan

        plan_obj = Plan.objects.filter(code=plan_code).first()
        if not plan_obj:
            logger.warning(
                f"No Plan found with code '{plan_code}' for tenant {tenant_obj.schema_name}. Skipping tenant config seeding."
            )
            return None, settings

        # Update tenant's plan_name to match the actual Plan.name
        # This corrects mismatches like GENIUS sending "Internal" instead of "RESIDO Standard Plan"
        if tenant_obj.plan_name != plan_obj.name:
            tenant_obj.plan_name = plan_obj.name
            tenant_obj.save(update_fields=["plan_name"])

        plan_manager = PlanManager.init(plan_name=plan_obj.name, plan_obj=plan_obj)
        if not plan_manager:
            logger.warning(
                f"Failed to initialize PlanManager for plan '{plan_obj.name}'. Skipping tenant config seeding."
            )
            return None, settings

        module_composition = plan_manager.get_module_composition()
        cls.create_subs_record_for_backward_compatibility(
            tenant_obj=tenant_obj, plan_obj=plan_manager.plan_obj
        )
        return module_composition, settings

    # RESIDO: No HDOC subscription needed - removed for RESIDO

    @staticmethod
    def get_default_modules_detail_from_plan_composition_and_settings(
        module_composition, settings
    ):
        """
        Map subscribed modules to tenant configuration flags

        RESIDO modules and their corresponding config fields:
        - PYMT (Payments) -> is_payment_processing_enabled
        - MAINT (Maintenance) -> is_maintenance_module_enabled
        - BOOK (Bookings) -> is_booking_module_enabled
        - ANALYT (Analytics) -> is_analytics_enabled
        - DOCS (Digital Forms) -> is_digital_forms_enabled
        """
        tenant_config_data = {
            "is_payment_processing_enabled": False,
            "is_maintenance_module_enabled": False,
            "is_booking_module_enabled": False,
            "is_analytics_enabled": False,
            "is_digital_forms_enabled": False,
        }

        # Map module codes to configuration fields
        module_config_mapping = {
            "PYMT": "is_payment_processing_enabled",
            "MAINT": "is_maintenance_module_enabled",
            "BOOK": "is_booking_module_enabled",
            "ANALYT": "is_analytics_enabled",
            "DOCS": "is_digital_forms_enabled",
        }

        # Check which modules are subscribed and set config accordingly
        for module in module_composition:
            module_code = module.get("code")
            module_subscribed = module.get("subscribed")

            if module_code in module_config_mapping and module_subscribed:
                config_field = module_config_mapping[module_code]
                tenant_config_data[config_field] = True

        # Process product settings if provided
        if settings:
            # Add setting-based configuration here as needed
            # Example:
            # setting_manager = ProductSettingManager(settings_data=settings)
            # auto_billing = setting_manager.is_setting_enabled("auto_billing")
            pass

        return tenant_config_data

    @classmethod
    def append_region_specific_config_items(cls, tenant_obj, tenant_config_data):
        """
        Add region-specific configurations for property management

        Different regions may have different regulatory requirements,
        payment processing needs, or feature availability.
        """
        if tenant_obj.country == "US":
            # US-specific configurations
            tenant_config_data["payment_grace_period_days"] = 5
            tenant_config_data["late_fee_enabled"] = True
            tenant_config_data["auto_payment_reminder_days"] = 3
            tenant_config_data["resident_portal_enabled"] = True
            tenant_config_data["self_service_enabled"] = True

        elif tenant_obj.country == "IN":
            # India-specific configurations
            tenant_config_data["payment_grace_period_days"] = 7
            tenant_config_data[
                "late_fee_enabled"
            ] = False  # May have different regulations
            tenant_config_data["auto_payment_reminder_days"] = 5
            tenant_config_data["resident_portal_enabled"] = True
            tenant_config_data["self_service_enabled"] = True

        else:
            # Default configurations for other regions
            tenant_config_data["payment_grace_period_days"] = 5
            tenant_config_data["late_fee_enabled"] = False
            tenant_config_data["auto_payment_reminder_days"] = 3
            tenant_config_data["resident_portal_enabled"] = True
            tenant_config_data["self_service_enabled"] = True

        return tenant_config_data

    @classmethod
    def upsert_tenant_config(cls, tenant_obj, module_composition, settings):
        """
        Create or update tenant configuration based on subscription

        This method:
        1. Maps subscribed modules to feature flags
        2. Applies region-specific configurations
        3. Persists config to database

        Args:
            tenant_obj: The tenant (HealthCareCustomer) instance
            module_composition: List of modules from the subscription plan
            settings: Optional product settings from the plan

        Returns:
            dict: The final tenant configuration data
        """
        # Get base configuration from subscribed modules
        tenant_config_data = (
            cls.get_default_modules_detail_from_plan_composition_and_settings(
                module_composition=module_composition, settings=settings
            )
        )

        # Apply region-specific settings
        tenant_config_data = cls.append_region_specific_config_items(
            tenant_obj=tenant_obj, tenant_config_data=tenant_config_data
        )

        # Persist configuration to database
        config_instance, created = HealthCareCustomerConfig.objects.update_or_create(
            customer=tenant_obj, defaults=tenant_config_data
        )

        return tenant_config_data
