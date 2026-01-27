from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.serializers import ValidationError

from common.helix_pagination import StandardPageNumberPagination
from common.response import StandardAPIResponse


class BulkUpdateMixin:
    primary_field = "id"

    def validate_ids(self, data, unique=True):
        if isinstance(data, list):
            ids_list = [x[self.primary_field] for x in data]
            if unique and len(ids_list) != len(set(ids_list)):
                raise ValidationError(
                    "Multiple updates to a single {} found".format(self.primary_field)
                )
            return ids_list
        return [data]

    def update(self, request, *args, **kwargs):
        ids = self.validate_ids(request.data)
        instances = self.get_queryset(ids=ids)
        serializer = self.get_serializer(
            instances, data=request.data, partial=False, many=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return serializer.data

    def perform_update(self, serializer):
        serializer.save()


class BasePaginatedViewMixin:
    def _get_paginated_api_response(self, request, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self._get_api_response(request, queryset, serializer)

    def _get_api_response(self, request, queryset, serializer):
        response_data = (
            {
                "values": serializer.data,
                "pagination": {
                    "page": int(request.query_params.get("page", 1)),
                    "per_page": int(
                        request.query_params.get(
                            "per_page", self.pagination_class.page_size
                        )
                    ),
                    "more": self.get_paginated_response(serializer.data).data.get(
                        "next"
                    )
                    is not None,
                    "total": queryset.count(),
                },
            },
        )
        return response_data


class StandardUpdateAPIMixin(generics.UpdateAPIView):
    def put(self, request, *args, **kwargs):
        response_obj = super().put(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)

    def patch(self, request, *args, **kwargs):
        response_obj = super().patch(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)


class StandardRetieveAPIMixin(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        response_obj = super().get(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)


class StandardRetrieveUpdateAPIMixin(
    StandardRetieveAPIMixin, StandardUpdateAPIMixin, generics.DestroyAPIView
):
    pass


class StandardListBulkCreateAPIMixin(generics.ListCreateAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering = ("-created_on",)
    pagination_class = StandardPageNumberPagination

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return StandardAPIResponse(
            data=serializer.data, headers=headers, status=status.HTTP_201_CREATED
        )


class StandardListAPIMixin(generics.ListAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering = ("-created_on",)
    pagination_class = StandardPageNumberPagination

    def get(self, request, *args, **kwargs):
        response_obj = super().get(request, *args, **kwargs)
        if isinstance(response_obj, StandardAPIResponse):
            return response_obj
        return StandardAPIResponse(
            data={
                "values": response_obj.data,
                "pagination": {
                    "page": 0,
                    "per_page": None,
                    "total": len(response_obj.data),
                    "more": None,
                },
            },
            status=status.HTTP_200_OK,
        )


class StandardCreateAPIMixin(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        response_obj = super().post(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)


class StandardListCreateAPIMixin(generics.ListCreateAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering = ("-updated_on",)
    pagination_class = StandardPageNumberPagination

    def post(self, request, *args, **kwargs):
        response_obj = super().post(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)

    def get(self, request, *args, **kwargs):
        response_obj = super().get(request, *args, **kwargs)
        if isinstance(response_obj, StandardAPIResponse):
            return response_obj
        return StandardAPIResponse(
            data={
                "values": response_obj.data,
                "pagination": {
                    "page": 0,
                    "per_page": None,
                    "total": len(response_obj.data),
                    "more": None,
                },
            },
            status=status.HTTP_200_OK,
        )


class StandardDestroyAPIMixin(generics.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        response_obj = super().delete(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)


class HelixSerializerMixin:
    @property
    def _readable_fields(self):
        min_fields = []
        yield_only_min_fields = self.context.get("min_view", False)
        if yield_only_min_fields:
            min_fields = getattr(self.Meta, "min_view_fields", [])
        for field_name in self.fields:
            if yield_only_min_fields and field_name not in min_fields:
                continue
            field = self.fields[field_name]
            if not field.write_only:
                yield field


class StandardRetrieveAPIMixin(generics.RetrieveAPIView):
    def get(self, request, *args, **kwargs):
        response_obj = super().get(request, *args, **kwargs)
        return StandardAPIResponse.from_response(response_obj=response_obj)


class CountAPIMixin(generics.GenericAPIView):
    def __init__(self, *args, **kwargs):
        """
        count_status_to_field_condition_map = {
            "all": {
                "field": "id",
                "condition": {}
            },
            "active": {
                "field": "status",
                "condition": {"status": True}
            }
        }
        """
        if not hasattr(self, "queryset") or not hasattr(
            self, "count_label_to_field_condition_map"
        ):
            raise AttributeError(
                "Count api not configured properly. Please make sure the required attributes are defined: queryset, count_field_name, count_field_values"
            )
        return super().__init__(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        q = self.queryset
        label_condition_map = self.count_label_to_field_condition_map
        for label, obj in label_condition_map.items():
            if "field" not in obj.keys() or "condition" not in obj.keys():
                continue
            params = {
                label
                + "__count": Count(obj.get("field"), filter=Q(**obj.get("condition")))
            }
            q = q.annotate(**params)
        aggregate_params = [
            Sum(label + "__count") for label in label_condition_map.keys()
        ]
        q = q.aggregate(*aggregate_params)
        return StandardAPIResponse(
            data={
                label: (
                    q.get(label + "__count__sum", 0)
                    if q.get(label + "__count__sum")
                    else 0
                )
                for label in label_condition_map.keys()
            },
            status=status.HTTP_200_OK,
        )
