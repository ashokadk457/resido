from customer_backend.managers.tenant import TenantManager
from rest_framework.permissions import AllowAny

from hb_core.mixins import StandardListCreateAPIMixin
from helixauth.authentication.composite.guest import GuestCompositeAuthentication
from subscriptions.models.subscription import TenantSubscription
from subscriptions.serializers.subscription import TenantSubscriptionSerializer


class TenantSubscriptionsListCreateAPIView(StandardListCreateAPIMixin):
    authentication_classes = [GuestCompositeAuthentication]
    permission_classes = [AllowAny]
    serializer_class = TenantSubscriptionSerializer

    def get_queryset(self):
        return TenantSubscription.objects.filter(
            tenant=TenantManager().tenant_obj, active=True
        )
