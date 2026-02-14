"""
Serializers for RESIDO subscription models

Provides JSON representation of Plan and ProductSetting models
for API responses to GENIUS during customer onboarding.

ARCHITECTURE NOTE:
- RESIDO serializers only expose Plans and ProductSettings
- TenantSubscription is managed by GENIUS, not RESIDO
"""
from rest_framework import serializers
from hb_core.serializers import StandardModelSerializer

from subscriptions.models.plan import Plan
from subscriptions.models.product_setting import ProductSetting


class PlanSerializer(serializers.ModelSerializer):
    """
    Full plan serializer including all fields

    Used by authenticated S2S requests (e.g., GENIUS fetching plans)
    """

    class Meta:
        model = Plan
        fields = "__all__"


class PlanMiniSerializer(StandardModelSerializer):
    """
    Minimal plan serializer for basic plan information

    Used in list views or where only essential fields are needed
    """

    class Meta:
        model = Plan
        fields = ["id", "name", "code", "active", "seeded"]


class ProductSettingSerializer(StandardModelSerializer):
    """
    Product setting serializer

    Exposes global RESIDO subscription settings
    """

    class Meta:
        model = ProductSetting
        fields = "__all__"
