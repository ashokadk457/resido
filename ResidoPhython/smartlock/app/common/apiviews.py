from django.db.models import CharField, F, Q, Value
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.constants import GENIUS_DOMAIN
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.managers.service import ServiceManager
from common.mixins import (
    BulkUpdateMixin,
    StandardListAPIMixin,
    StandardRetieveAPIMixin,
    StandardRetrieveUpdateAPIMixin,
)
from common.models import HealthCareCustomer, Country, State, PetSpecies, PetBreed
from common.response import StandardAPIResponse
from common.serializers import (
    HealthCareCustomerSerializer,
    TenantSerializer,
    CountrySerializer,
    StateSerializer,
    PetSpeciesSerializer,
    PetBreedSerializer,
)
from common.utils.general import is_helix_user_request
from external.hus.core import HelixUtilityService
from helixauth.models import HelixUser
from residents.models import Resident


class NoPagination(PageNumberPagination):
    page_size = None


class AddressSearch(APIView):
    permission_classes = [
        AllowAny,
    ]

    def get(self, request):
        text = request.query_params.get("text", None)
        country = request.query_params.get("country", "USA")
        if text is None:
            return Response({"message": ERROR_DETAILS["req_param_missing"]}, status=400)
        params = {"text": text, "boundary.country": country}
        helix_service = HelixUtilityService()
        response = helix_service.get("address/autocomplete", params=params)
        return response


class HealthCareCustomerList(StandardListAPIMixin):
    permission_classes = [
        AllowAny,
    ]

    def get_queryset(self):
        return HealthCareCustomer.objects.filter(id=self.request.tenant.id)

    def get_serializer_class(self):
        if is_helix_user_request(self.request):
            return HealthCareCustomerSerializer
        return TenantSerializer


class HealthCareCustomerDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if is_helix_user_request(self.request):
            return HealthCareCustomerSerializer
        return TenantSerializer

    def get_queryset(self):
        return HealthCareCustomer.objects.filter(id=self.request.tenant.id)

    def get(self, request):
        serializer = self.get_serializer_class()
        tenant_data = serializer(request.tenant).data

        # Add genius_domain to response
        tenant_data["genius_domain"] = GENIUS_DOMAIN

        return StandardAPIResponse(data=tenant_data, status=status.HTTP_200_OK)

    def put(self, request):
        if not is_helix_user_request(self.request):
            raise StandardAPIException(
                code="method_not_allowed",
                detail=ERROR_DETAILS["method_not_allowed"],
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        data = request.data
        serializer = self.get_serializer_class()
        data.pop("logo_details", None)
        data.pop("favicon_details", None)
        data.pop("id", None)
        logo = data.pop("logo", None)
        favicon = data.pop("favicon", None)
        if logo or favicon:
            asset = request.tenant.asset
            asset.logo_id = logo
            asset.favicon_id = favicon
            asset.save()
        HealthCareCustomer.objects.filter(id=request.tenant.id).update(**data)
        tenant = HealthCareCustomer.objects.get(id=request.tenant.id)
        return StandardAPIResponse(
            data=serializer(tenant).data, status=status.HTTP_200_OK
        )
        return super().put(request)


class ServiceInfoView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get(request):
        response_data = ServiceManager().get_service_info()
        return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)


class BulkUpdateAPIView(BulkUpdateMixin, generics.GenericAPIView):
    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data", {}), list):
            kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self, ids=None):
        if ids is not None:
            raise NotImplementedError(
                "Please implement get_queryset(self, ids=None) method in your API View to fetch multible instances"
            )
        return super().get_queryset()

    def put(self, request, *args, **kwargs):
        try:
            response_data = self.update(request, *args, **kwargs)
            return StandardAPIResponse(data=response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return StandardAPIResponse(data=e, exception=True)


class SearchPatientsAndProvidersAPIView(APIView):
    """
    API to search for residousers and providers by first or last name.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("search", "").strip()

        if not query:
            return StandardAPIException(
                data={"error": "Query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Search residousers
        patients = (
            Resident.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            .annotate(
                email_address=F("email"),  # Rename email to email_address
                content_type=Value(47, output_field=CharField()),  # Add content type
            )
            .values("id", "first_name", "last_name", "email_address", "content_type")
        )

        # Search providers
        providers = (
            HelixUser.objects.filter(
                Q(first_name__icontains=query) | Q(last_name__icontains=query)
            )
            .annotate(
                email_address=F("email"),  # Rename email to email_address
                content_type=Value(3, output_field=CharField()),  # Add content type
            )
            .values("id", "first_name", "last_name", "email_address", "content_type")
        )

        # Combine and sort by first name
        results = sorted(
            list(patients) + list(providers),
            key=lambda x: x["first_name"].lower(),
        )

        return StandardAPIResponse(data=results, status=status.HTTP_200_OK)


class CountryListCreateAPIView(StandardListAPIMixin):
    search_fields = (
        "name",
        "code",
    )
    filterset_fields = (
        "name",
        "code",
    )
    permission_classes = [AllowAny]
    allowed_methods_to_resident = {"get": True, "post": True}
    ordering = ("name",)
    queryset = Country.objects.all()
    pagination_class = None
    serializer_class = CountrySerializer


class CountryRetrieveUpdateAPIView(StandardRetieveAPIMixin):
    permission_classes = [AllowAny]
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class StateListCreateAPIView(StandardListAPIMixin):
    search_fields = ("name",)
    filterset_fields = ("country__code", "name")
    permission_classes = [AllowAny]
    allowed_methods_to_resident = {"get": True, "post": True}
    ordering = ("name",)
    queryset = State.objects.all()
    pagination_class = None
    serializer_class = StateSerializer


class StateRetrieveUpdateAPIView(StandardRetieveAPIMixin):
    permission_classes = [AllowAny]
    queryset = State.objects.all()
    serializer_class = StateSerializer


class PetSpeciesListCreateAPIView(StandardListAPIMixin):
    search_fields = ("name", "code")
    filterset_fields = ("name", "code", "is_active")
    permission_classes = [AllowAny]
    allowed_methods_to_resident = {"get": True, "post": True}
    ordering = ("name",)
    queryset = PetSpecies.objects.all()
    pagination_class = None
    serializer_class = PetSpeciesSerializer


class PetSpeciesRetrieveUpdateAPIView(StandardRetieveAPIMixin):
    permission_classes = [AllowAny]
    queryset = PetSpecies.objects.all()
    serializer_class = PetSpeciesSerializer


class PetBreedListCreateAPIView(StandardListAPIMixin):
    search_fields = ("name", "code")
    filterset_fields = ("species__code", "species__id", "name", "code", "is_active")
    permission_classes = [AllowAny]
    allowed_methods_to_resident = {"get": True, "post": True}
    ordering = ("name",)
    queryset = PetBreed.objects.all()
    pagination_class = None
    serializer_class = PetBreedSerializer


class PetBreedRetrieveUpdateAPIView(StandardRetieveAPIMixin):
    permission_classes = [AllowAny]
    queryset = PetBreed.objects.all()
    serializer_class = PetBreedSerializer
