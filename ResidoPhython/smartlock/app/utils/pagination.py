"""
Pagination utilities for API responses
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for consistent pagination across API
    """

    page_size = 50
    page_size_query_param = "page_size"
    page_size_query_description = "Number of results to return per page."
    max_page_size = 1000
    page_query_param = "page"
    page_query_description = "A page number within the paginated result set."

    def get_paginated_response(self, data):
        """
        Return paginated response in custom format
        """
        return Response(
            OrderedDict(
                [
                    ("success", True),
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("page", self.page.number),
                    ("page_size", self.page_size),
                    ("total_pages", self.page.paginator.num_pages),
                    ("results", data),
                ]
            )
        )
