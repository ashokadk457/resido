from common.filters import StandardAPIFilter
from payments.models import BillCancellationCodeComposition


class BillCancellationCodeCompositionFilter(StandardAPIFilter):
    class Meta:
        model = BillCancellationCodeComposition
        fields = ("id", "cancellation_code", "active")
