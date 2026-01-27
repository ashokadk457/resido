from rest_framework import serializers

from subscriptions.models.subscription import TenantSubscription
from subscriptions.serializers.plan import PlanSerializer


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer()

    class Meta:
        model = TenantSubscription
        fields = "__all__"
