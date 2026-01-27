from django.core.paginator import InvalidPage
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

from common.response import StandardAPIResponse


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000


class StandardPageNumberPagination(PageNumberPagination):
    page_size_query_param = "per_page"

    def get_paginated_response(self, data):
        return StandardAPIResponse(
            data={
                "values": data,
                "pagination": {
                    "page": self.page.number,
                    "per_page": self.page.paginator.per_page,
                    "total": self.page.paginator.count,
                    "more": self.page.has_next(),
                },
            },
            status=status.HTTP_200_OK,
        )


class CustomPaginationForPostMethod(StandardPageNumberPagination):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.internal_paginator = None
        self.page_number = kwargs.get("page_number")
        self.page_size = kwargs.get("page_size", self.page_size)
        self.page = None

    def custom_paginate_queryset(self, queryset):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        if not self.page_size:
            return None

        self.internal_paginator = self.django_paginator_class(queryset, self.page_size)

        try:
            self.page = self.internal_paginator.page(self.page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=self.page_number, message=str(exc)
            )
            raise NotFound(msg)

        if self.internal_paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        return list(self.page)

    def get_approximate_total_num(self):
        if self.internal_paginator is None:
            return

        return self.internal_paginator.num_pages * int(self.page_size)


class CustomPagination(PageNumberPagination):
    page_size = None  # Disable pagination by default
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return StandardAPIResponse(
            data={
                "values": data,
                "pagination": {
                    "page": self.page.number,
                    "per_page": self.page.paginator.per_page,
                    "total": self.page.paginator.count,
                    "more": self.page.has_next(),
                },
            },
            status=status.HTTP_200_OK,
        )

    def get_non_paginated_response(self, queryset, serializer):
        return {
            "values": serializer.data,
            "pagination": {
                "page": None,
                "per_page": None,
                "more": None,
                "total": queryset.count(),
            },
        }
