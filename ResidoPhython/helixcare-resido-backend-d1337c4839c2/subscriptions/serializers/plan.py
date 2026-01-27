from hb_core.serializers import StandardModelSerializer
from rest_framework import serializers

from customer_backend.serializers.rla import (
    ModuleSerializer,
    SubModuleCompositionSerializer,
)
from subscriptions.managers.plan import PlanManager
from subscriptions.models.plan import Plan, PlanModuleComposition


class PlanModuleCompositionSerializer(serializers.ModelSerializer):
    module = ModuleSerializer()
    submodule = SubModuleCompositionSerializer()

    class Meta:
        model = PlanModuleComposition
        fields = "__all__"


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"

    @staticmethod
    def get_module_composition(plan_obj):
        plan_manager = PlanManager(plan_obj=plan_obj)
        return plan_manager.get_module_composition()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        module_composition = self.get_module_composition(plan_obj=instance)
        representation["module_composition"] = module_composition
        return representation


class PlanMiniSerializerV2(StandardModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "code", "active", "seeded"]
