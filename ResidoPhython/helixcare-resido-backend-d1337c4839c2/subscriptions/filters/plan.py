from hb_core.filters import StandardAPIFilter
from subscriptions.models.plan import Plan


class PlanFilter(StandardAPIFilter):
    class Meta:
        model = Plan
        fields = ["id", "name", "code", "seeded", "active"]
