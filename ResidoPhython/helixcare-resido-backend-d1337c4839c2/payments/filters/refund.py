import django_filters

from payments.models import BillRefundRequest


class BillRefundRequestFilter(django_filters.FilterSet):
    class Meta:
        model = BillRefundRequest
        fields = ("id", "status", "process", "refund_type")
