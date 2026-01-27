import django_filters
from django.db.models import Q


class StandardAPIFilter(django_filters.FilterSet):
    id = django_filters.CharFilter(method="filter_by_id")

    @staticmethod
    def _filter_csv(queryset, name, value, attr):
        query = Q()
        for _val in value.split(","):
            query |= Q(**{attr: _val})
        return queryset.filter(query)

    @staticmethod
    def filter_by_id(queryset, name, value):
        return queryset.filter(id=value)


class CaseInsensitiveInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        values = [v.strip().lower() for v in value if v.strip()]
        query = Q()
        for v in values:
            query |= Q(**{f"{self.field_name}__iexact": v})
        return qs.filter(query)
