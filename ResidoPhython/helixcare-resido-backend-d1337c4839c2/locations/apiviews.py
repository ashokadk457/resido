from django.db.models.aggregates import Count
from django.db.transaction import atomic
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework import generics, status
from rest_framework.views import APIView
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    CountAPIMixin,
)
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from helixauth.authentication.composite.guest import ResidentCompositeAuthentication
from common.response import StandardAPIResponse
from common.helix_pagination import CustomPagination
from common.utils.general import is_valid_uuid
from staff.models import HelixStaff
from locations.filters import (
    UnitFilter,
    AmenityFilter,
    LocationFilter,
    ParkingLevelFilter,
    ParkingSlotFilter,
    MyUnitFilter,
)
from locations.models import (
    Location,
    Property,
    Building,
    Floor,
    Unit,
    Customer,
    Amenity,
    ParkingLevel,
    ParkingZone,
    ParkingSlot,
)
from locations.serializers import (
    CustomerSerializer,
    LocationSerializer,
    LocationCreateUpdateSerializer,
    PropertySerializer,
    PropertyCreateUpdateSerializer,
    PropertyTabStatusSerializer,
    PropertyEntityCountSerializer,
    BuildingSerializer,
    FloorSerializer,
    UnitSerializer,
    AmenitySerializer,
    LocationDetailSerializer,
    BuildingDetailSerializer,
    FloorDetailSerializer,
    UnitDetailSerializer,
    ParkingLevelSerializer,
    ParkingZoneSerializer,
    ParkingSlotSerializer,
    ParkingSlotBulkCreateSerializer,
    ParkingZoneBulkCreateSerializer,
    MyUnitSerializer,
    MyUnitDetailSerializer,
)


class LocationListCreate(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "name",
        "short_name",
        "display_id",
        "address",
        "address_1",
        "city",
        "state",
        "zipcode",
        "country",
    )
    filterset_class = LocationFilter
    serializer_class = LocationSerializer
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    allowed_methods_to_resident = {"get": True}
    entity = "Location"

    def paginate_queryset(self, queryset):
        if "trimmed" in self.request.GET.keys():
            return None
        return super().paginate_queryset(queryset)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LocationCreateUpdateSerializer
        return LocationSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Location.objects.for_current_user().order_by("-created_on")
        return Location.objects.for_current_user().order_by("-created_on")


class LocationDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission,
    ]
    serializer_class = LocationDetailSerializer
    entity = "Location"

    def get_queryset(self):
        queryset = Location.objects.for_current_user().prefetch_related(
            "building__floor"
        )
        return queryset


class PropertyList(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = (
        "name",
        "short_name",
        "display_id",
    )
    filter_fields = (
        "name",
        "short_name",
        "display_id",
        "id",
        "city",
        "zipcode",
        "state",
    )
    serializer_class = PropertySerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "Property"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PropertyCreateUpdateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = Property.objects.for_current_user().order_by("-created_on")
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)

        customer_id = self.request.query_params.get("customer")
        if customer_id and is_valid_uuid(customer_id):
            queryset = queryset.filter(customer_id=str(customer_id))

        return queryset


class PropertyDetail(StandardRetrieveUpdateAPIMixin):
    permission_classes = [
        HelixUserBasePermission | IsAuthenticatedResidentPermission,
    ]
    serializer_class = PropertyCreateUpdateSerializer
    entity = "Property"
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        queryset = Property.objects.for_current_user()
        return queryset


class PropertySavedTabsStatus(generics.RetrieveAPIView):
    permission_classes = [HelixUserBasePermission]
    serializer_class = PropertyTabStatusSerializer
    entity = "Property"

    def get_queryset(self):
        return Property.objects.for_current_user()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)


class PropertyEntityCountAPIView(generics.RetrieveAPIView):
    permission_classes = [HelixUserBasePermission]
    serializer_class = PropertyEntityCountSerializer
    entity = "Property"

    def get_queryset(self):
        return Property.objects.for_current_user()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)


class LocationTrimmedView(generics.ListAPIView):
    serializer_class = (
        LocationSerializer  # Dummy ; not using this for response ; added for permission
    )
    permission_classes = [HelixUserBasePermission]

    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["property__name"]
    pagination_class = CustomPagination

    entity = "Location"

    def get_queryset(self):
        return (
            Location.objects.for_current_user()
            .select_related("property", "property__customer")
            .values(
                "id",
                "name",
                "address",
                "property__id",
                "property__name",
                "property__customer__id",
                "property__customer__name",
            )
        )

    def group_by_property(self, raw_locations):
        property_locations_map = {}

        for rl in raw_locations:
            if rl["property__id"] not in property_locations_map:
                property_locations_map[rl["property__id"]] = []
            property_locations_map[rl["property__id"]].append(rl)

        return [
            {
                "property_id": rls[0]["property__id"],
                "customer_id": rls[0]["property__customer__id"],
                "customer_name": rls[0]["property__customer__name"],
                "property_name": rls[0]["property__name"],
                "locations": [
                    {
                        "location_id": rl["id"],
                        "location_name": rl["name"],
                        "location_address": rl["address"],
                    }
                    for rl in rls
                ],
            }
            for rls in property_locations_map.values()
        ]

    def get(self, request):
        page_param = self.request.query_params.get("page", None)
        queryset = self.filter_queryset(self.get_queryset())

        if page_param:
            page = self.paginate_queryset(queryset)
            if page is not None:
                grouped_data = self.group_by_property(page)
                return self.get_paginated_response(grouped_data)

        grouped_data = self.group_by_property(queryset)
        return StandardAPIResponse(data=grouped_data, status=status.HTTP_200_OK)


class CustomersListCreate(StandardListCreateAPIMixin):
    search_fields = (
        "name",
        "short_name",
        "display_id",
        "email",
        "phone",
        "work_phone",
    )
    filterset_fields = (
        "name",
        "short_name",
        "display_id",
        "email",
        "city",
        "state",
        "zipcode",
        "status",
        "is_active",
    )
    permission_classes = (HelixUserBasePermission,)
    entity = "Customer"
    ordering_fields = ["created_on", "property_count", "name"]
    ordering = ["-created_on"]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        return Customer.objects.for_current_user().annotate(
            property_count=Count("property")
        )

    @atomic
    def perform_create(self, serializer):
        helix_staff = serializer.initial_data.get("staff_id", None)
        if Customer.objects.filter(
            email__iexact=serializer.initial_data["email"]
        ).exists():
            raise StandardAPIException(
                code="email_already_exists",
                detail=ERROR_DETAILS["email_already_exists"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if helix_staff:
            try:
                helix_staff_object = HelixStaff.objects.get(id=helix_staff)
            except HelixStaff.DoesNotExist:
                raise StandardAPIException(
                    code="no_active_user",
                    detail=ERROR_DETAILS["no_active_user"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        super().perform_create(serializer)
        if helix_staff:
            helix_staff_object.customers.add(serializer.instance)


class CustomersDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = CustomerSerializer
    queryset = Customer.objects.for_current_user()
    entity = "Customer"

    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class CustomerCountAPIView(CountAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    entity = "Customer"
    queryset = Customer.objects.for_current_user()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "active": {
            "field": "is_active",
            "condition": {"is_active": True, "status": "Y"},
        },
        "inactive": {"field": "is_active", "condition": {"is_active": False}},
    }


class BuildingListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Building.objects.for_current_user()
    entity = "Building"
    search_fields = (
        "name",
        "display_id",
        "year_built",
    )
    filterset_fields = (
        "display_id",
        "total_floors",
        "year_built",
        "location",
    )
    serializer_class = BuildingSerializer
    ordering_fields = ["created_on", "year_built", "total_floors", "name"]
    ordering = ["-created_on"]
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        return Building.objects.for_current_user().prefetch_related("floor")


class BuildingDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = BuildingDetailSerializer
    queryset = Building.objects.for_current_user()
    entity = "Building"
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        return Building.objects.for_current_user().prefetch_related("floor")


class FloorListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Floor.objects.for_current_user()
    serializer_class = FloorSerializer
    entity = "Floor"
    search_fields = (
        "description",
        "display_id",
        "floor_number",
    )
    filterset_fields = (
        "floor_number",
        "display_id",
        "building",
    )
    ordering_fields = ["created_on", "floor_number"]
    ordering = ["-created_on"]
    allowed_methods_to_resident = {"get": True}

    def get_serializer_class(self):
        if self.request.method == "POST":
            from locations.serializers import FloorCreateUpdateSerializer

            return FloorCreateUpdateSerializer
        return self.serializer_class


class FloorDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = FloorDetailSerializer
    queryset = Floor.objects.for_current_user()
    entity = "Floor"
    allowed_methods_to_resident = {"get": True}

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            from locations.serializers import FloorCreateUpdateSerializer

            return FloorCreateUpdateSerializer
        return self.serializer_class


class UnitListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Unit.objects.for_current_user()
    serializer_class = UnitSerializer
    entity = "Unit"
    search_fields = (
        "unit_number",
        "display_id",
        "furnished_price",
        "unfurnished_price",
        "hoa_fee",
        "unit_size",
        "floor_plan",
    )
    filterset_class = UnitFilter
    ordering_fields = [
        "created_on",
        "furnished_price",
        "unfurnished_price",
    ]
    ordering = ["-created_on"]
    allowed_methods_to_resident = {"get": True}


class UnitDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = UnitDetailSerializer
    queryset = Unit.objects.for_current_user()
    entity = "Unit"
    allowed_methods_to_resident = {"get": True}


class AmenityListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Amenity.objects.for_current_user()
    serializer_class = AmenitySerializer
    entity = "Amenity"
    search_fields = (
        "name",
        "display_id",
        "capacity",
        "building__name",
    )
    filterset_class = AmenityFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-created_on"]


class AmenityDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = AmenitySerializer
    queryset = Amenity.objects.for_current_user()
    entity = "Amenity"

    def get_serializer_class(self):
        """Use AmenityDetailSerializer for retrieve, AmenitySerializer for update"""
        if self.request.method == "GET":
            from locations.serializers import AmenityDetailSerializer

            return AmenityDetailSerializer
        return self.serializer_class


class ParkingLevelListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = (HelixUserBasePermission,)
    queryset = ParkingLevel.objects.for_current_user()
    serializer_class = ParkingLevelSerializer
    entity = "ParkingLevel"
    search_fields = ("level_name",)
    filterset_class = ParkingLevelFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-updated_on"]


class ParkingLevelDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = ParkingLevelSerializer
    queryset = ParkingLevel.objects.for_current_user()
    entity = "ParkingLevel"


class ParkingZoneListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = (HelixUserBasePermission,)
    queryset = ParkingZone.objects.for_current_user()
    serializer_class = ParkingZoneSerializer
    entity = "ParkingZone"
    search_fields = ("name",)
    filterset_fields = (
        "is_active",
        "zone_type",
    )
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-updated_on"]


class ParkingZoneDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = ParkingZoneSerializer
    queryset = ParkingZone.objects.for_current_user()
    entity = "ParkingZone"


class ParkingZoneBulkCreateAPIView(APIView):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = ParkingZoneBulkCreateSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created_zones = serializer.save()
        if created_zones and isinstance(created_zones[0], list):
            created_zones = [zone for sublist in created_zones for zone in sublist]
        return StandardAPIResponse(
            {
                "message": f"{len(created_zones)} parking zones created successfully",
                "count": len(created_zones),
            },
            status=status.HTTP_201_CREATED,
        )


class ParkingSlotListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    queryset = ParkingSlot.objects.for_current_user()
    serializer_class = ParkingSlotSerializer
    entity = "ParkingSlot"
    search_fields = ("zone__name",)
    filterset_class = ParkingSlotFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-updated_on"]


class ParkingSlotBulkCreateAPIView(APIView):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = ParkingSlotBulkCreateSerializer

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def post(self, request):
        slots_data = request.data.get("slots", [])
        if not slots_data:
            raise StandardAPIException(
                code="slot_data_not_provided",
                detail=ERROR_DETAILS["slot_data_not_provided"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=slots_data, many=True)
        serializer.is_valid(raise_exception=True)
        created_slots = serializer.save()
        if created_slots and isinstance(created_slots[0], list):
            created_slots = [slot for sublist in created_slots for slot in sublist]

        return StandardAPIResponse(
            {
                "message": f"{len(created_slots)} parking slots created successfully",
                "count": len(created_slots),
            },
            status=status.HTTP_201_CREATED,
        )


class ParkingSlotDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    serializer_class = ParkingSlotSerializer
    queryset = ParkingSlot.objects.for_current_user()
    entity = "ParkingSlot"


class ParkingLevelCountAPIView(CountAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    entity = "ParkingLevel"
    queryset = ParkingLevel.objects.for_current_user()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "active": {"field": "is_active", "condition": {"is_active": True}},
        "inactive": {"field": "is_active", "condition": {"is_active": False}},
    }


class ParkingSlotCountAPIView(CountAPIMixin):
    permission_classes = (HelixUserBasePermission,)
    entity = "ParkingSlot"
    queryset = ParkingSlot.objects.for_current_user()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "active": {"field": "is_active", "condition": {"is_active": True}},
        "inactive": {"field": "is_active", "condition": {"is_active": False}},
    }


class MyPropertiesListAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    queryset = Unit.objects.for_current_user().filter(lease__isnull=False).distinct()
    serializer_class = MyUnitSerializer
    entity = "Unit"
    search_fields = (
        "unit_number",
        "floor__building__name",
        "floor__building__location__property__name",
    )
    filterset_class = MyUnitFilter
    ordering_fields = [
        "created_on",
        "updated_on",
    ]
    ordering = ["-updated_on"]


class MyPropertiesDetailAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    authentication_classes = [ResidentCompositeAuthentication]
    serializer_class = MyUnitDetailSerializer
    queryset = (
        Unit.objects.for_current_user()
        .select_related("floor__building__location__property__customer")
        .prefetch_related(
            "lease__other_occupants",
            "lease__late_fees",
            "lease__promotional_discount",
        )
    )
    entity = "Unit"
