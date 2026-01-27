from helixauth.authentication.composite.guest import GuestCompositeAuthentication
from .models import CPTData, Lookup, UIMetaData
from .serializers import (
    CPTDataSerializer,
    LookupSerializer,
    UIMetadataSerializer,
    LookupUpdateSerializer,
)
from rest_framework import generics
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from common.permissions import HelixUserBasePermission


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000


class LookupUpdateView(generics.UpdateAPIView):
    queryset = Lookup.objects.all()
    serializer_class = LookupUpdateSerializer
    permission_classes = (HelixUserBasePermission,)
    entity = "Lookup"


class LookupListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [GuestCompositeAuthentication]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["name", "code"]
    filter_fields = {"name": ["in", "exact"], "code": ["exact"]}
    queryset = Lookup.objects.filter(active=True)
    serializer_class = LookupSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class CPTCodeList(generics.ListAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["cpt_code", "description"]
    filter_fields = {"cpt_code": ["in", "exact"], "description": ["in", "exact"]}
    queryset = CPTData.objects.all()
    serializer_class = CPTDataSerializer
    permission_classes = (AllowAny,)
    pagination_class = LargeResultsSetPagination

    def create(self, request):
        pass


class CPTCodesDetail(generics.RetrieveAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = CPTDataSerializer
    entity = "CPTData"

    def get_queryset(self):
        queryset = CPTData.objects.all()
        return queryset


class UIMetadataList(generics.ListAPIView):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["active", "type"]
    filter_fields = ["active", "type"]
    queryset = UIMetaData.objects.all()
    serializer_class = UIMetadataSerializer
    permission_classes = (AllowAny,)
    pagination_class = LargeResultsSetPagination

    def create(self, request):
        pass
