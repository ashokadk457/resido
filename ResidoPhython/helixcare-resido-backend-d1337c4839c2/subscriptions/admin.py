# Register your models here.
from django.contrib import admin

from hb_core.utils.admin import StandardBaseAdmin
from subscriptions.managers.pcomp import PlanCompositionManager
from subscriptions.models.plan import Plan, PlanModuleComposition
from subscriptions.models.tier import Tier, TierComposition, TierMetric
from subscriptions.models.subscription import TenantSubscription
from subscriptions.models.product_setting import ProductSetting, ProductSettingValue


# Register your models here.
@admin.register(TenantSubscription)
class TenantSubscriptionAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "tenant",
        "plan_name",
        "tier",
        "start_date",
        "end_date",
        "expires_on",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    list_filter = ("plan", "active")
    search_fields = ("id",)

    def plan_name(self, obj):
        if obj.plan is None:
            return

        plan_ref, link_text = (
            str(obj.plan.id),
            obj.plan.__str__(),
        )
        if not plan_ref:
            return plan_ref

        return self._get_admin_changelist_link(
            app="subscriptions",
            model="plan",
            obj_id=plan_ref,
            link_text=link_text,
        )


@admin.register(Plan)
class PlanAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "description",
        "seeded",
        "active",
        "created_on_ist",
        "updated_on_ist",
        "module_composition",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    list_filter = ("code", "active", "seeded")
    search_fields = ("id", "name")

    def module_composition(self, obj):
        plan_ref, link_text = (
            str(obj.id),
            "Check Modules",
        )
        if not plan_ref:
            return plan_ref

        return self._get_admin_changelist_link(
            app="subscriptions",
            model="planmodulecomposition",
            obj_id=plan_ref,
            link_text=link_text,
        )


@admin.register(PlanModuleComposition)
class PlanModuleCompositionAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "plan_name",
        "module",
        "submodule",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )
    ordering = ["-created_on"]
    list_per_page = 25
    list_filter = ("active", "plan")
    search_fields = ("id", "plan__id")
    actions = [PlanCompositionManager.unsubscribe, PlanCompositionManager.subscribe]

    def plan_name(self, obj):
        if obj.plan is None:
            return

        plan_ref, link_text = (
            str(obj.plan.id),
            obj.plan.__str__(),
        )
        if not plan_ref:
            return plan_ref

        return self._get_admin_changelist_link(
            app="subscriptions",
            model="plan",
            obj_id=plan_ref,
            link_text=link_text,
        )


@admin.register(Tier)
class TierAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "description",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )


@admin.register(TierMetric)
class TierMetricAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "module",
        "submodule",
        "code",
        "name",
        "description",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )


@admin.register(TierComposition)
class TierCompositionAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "tier",
        "tier_metric",
        "value",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )


@admin.register(ProductSetting)
class ProductSettingAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "name",
        "visible_name",
        "category",
        "default_value",
        "seeded",
        "active",
        "created_on_ist",
        "updated_on_ist",
    )
    list_per_page = 25
    list_filter = ("category", "active", "seeded")
    search_fields = ("id", "name", "visible_name")


@admin.register(ProductSettingValue)
class ProductSettingValueAdmin(StandardBaseAdmin):
    list_display = (
        "id",
        "customer_info",
        "setting_info",
        "value",
        "created_on_ist",
        "updated_on_ist",
    )
    list_per_page = 25
    list_filter = ("customer", "setting")
    search_fields = (
        "id",
        "customer__id",
        "setting__id",
    )

    def customer_info(self, obj):
        if obj.customer is None:
            return None
        customer_uuid, link_text = str(obj.customer.id), str(obj.customer.__str__())
        return self._get_admin_changelist_link(
            app="common",
            model="healthcarecustomer",
            obj_id=customer_uuid,
            link_text=link_text,
        )

    def setting_info(self, obj):
        if obj.setting is None:
            return None
        setting_id, link_text = str(obj.setting.id), str(obj.setting.__str__())
        return self._get_admin_changelist_link(
            app="subscriptions",
            model="productsetting",
            obj_id=setting_id,
            link_text=link_text,
        )
