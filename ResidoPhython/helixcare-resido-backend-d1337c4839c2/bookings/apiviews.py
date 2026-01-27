from rest_framework import generics, status
from common.mixins import StandardListCreateAPIMixin, StandardRetrieveUpdateAPIMixin
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.response import StandardAPIResponse
from common.utils.general import is_resident_request
from common.exception import StandardAPIException
from .models import (
    AmenitySlot,
    AmenityBlackoutPeriod,
    AmenityBooking,
    BookingStatus,
)
from .serializers import (
    AmenitySlotSerializer,
    BlackoutPeriodSerializer,
    BookingSerializerForStaff,
    BookingSerializerForTenant,
    BulkAmenitySlotCreationSerializer,
    BulkSlotCreationResultSerializer,
    AmenitiesAndReservationsSummarySerializer,
)
from .filters import AmenitySlotFilter, BlackoutPeriodFilter, BookingFilter
from bookings.managers.duplicate_booking import DuplicateBookingManager


class AmenitySlotListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = AmenitySlot.objects.for_current_user()
    entity = "AmenitySlot"
    search_fields = ["amenity__name", "display_id"]
    filterset_class = AmenitySlotFilter
    ordering_fields = ["slot_date", "slot_start_time"]
    ordering = ["slot_date", "slot_start_time"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            # Check if this is a bulk creation request or individual slot
            if self._is_bulk_request(self.request.data):
                return BulkAmenitySlotCreationSerializer
            return AmenitySlotSerializer
        return AmenitySlotSerializer

    @staticmethod
    def _is_bulk_request(data):
        bulk_keys = {
            "from_date",
            "to_date",
            "operating_start_time",
            "operating_end_time",
        }
        return bulk_keys.issubset(data.keys())

    def post(self, request, *args, **kwargs):
        if self._is_bulk_request(request.data):
            return self._handle_bulk_creation(request)
        return super().post(request, *args, **kwargs)

    def _handle_bulk_creation(self, request):
        serializer = BulkAmenitySlotCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            from locations.models import Amenity
            from bookings.managers.slots import AmenitySlotManager

            amenity_id = serializer.validated_data["amenity_id"]
            amenity = Amenity.objects.get(id=amenity_id)

            # Initialize manager
            manager = AmenitySlotManager(
                amenity=amenity,
                from_date=serializer.validated_data["from_date"],
                to_date=serializer.validated_data["to_date"],
                operating_start_time=serializer.validated_data["operating_start_time"],
                operating_end_time=serializer.validated_data["operating_end_time"],
                interval_minutes=serializer.validated_data.get("interval_minutes", 60),
                max_concurrent_bookings=serializer.validated_data.get(
                    "max_concurrent_bookings", 1
                ),
            )

            result = manager.generate_slots(
                delete_existing=serializer.validated_data.get("delete_existing", False)
            )

            response_data = {
                "created_count": len(result["created"]),
                "updated_count": len(result["updated"]),
                "error_count": len(result["errors"]),
                "errors": result["errors"],
                "summary": (
                    f"Created {len(result['created'])} slots, "
                    f"updated {len(result['updated'])} slots due to blackout"
                ),
            }

            response_serializer = BulkSlotCreationResultSerializer(response_data)
            return StandardAPIResponse(
                data=response_serializer.data, status=status.HTTP_201_CREATED
            )

        except Amenity.DoesNotExist:
            raise StandardAPIException(
                code="amenity_not_found",
                detail="Amenity not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            raise StandardAPIException(
                code="slot_generation_error",
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class AmenitySlotDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = AmenitySlot.objects.for_current_user()
    serializer_class = AmenitySlotSerializer
    entity = "AmenitySlot"


class BlackoutPeriodListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = AmenityBlackoutPeriod.objects.for_current_user()
    serializer_class = BlackoutPeriodSerializer
    entity = "BlackoutPeriod"
    search_fields = ["amenity__name", "reason"]
    filterset_class = BlackoutPeriodFilter
    ordering_fields = ["start_date"]
    ordering = ["start_date"]


class BlackoutPeriodDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = AmenityBlackoutPeriod.objects.for_current_user()
    serializer_class = BlackoutPeriodSerializer
    entity = "BlackoutPeriod"


class BookingListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True, "post": True}
    entity = "AmenityBooking"
    search_fields = [
        "amenity__name",
        "tenant__user__first_name",
        "tenant__user__last_name",
        "display_id",
    ]
    filterset_class = BookingFilter
    ordering_fields = ["booking_date", "requested_on"]
    ordering = ["-requested_on"]

    def get_queryset(self):
        qs = AmenityBooking.objects.for_current_user().select_related(
            "amenity", "amenity__building", "tenant", "tenant__user"
        )
        if is_resident_request(self.request):
            qs = qs.filter(tenant=self.request.user.resident)
        return qs

    def get_serializer_class(self):
        if is_resident_request(self.request):
            return BookingSerializerForTenant
        return BookingSerializerForStaff


class BookingDetailUpdate(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "AmenityBooking"

    def get_queryset(self):
        qs = AmenityBooking.objects.for_current_user()
        # Tenant sees only their own bookings
        if is_resident_request(self.request):
            qs = qs.filter(tenant=self.request.user.resident)
        return qs

    def get_serializer_class(self):
        if is_resident_request(self.request):
            return BookingSerializerForTenant
        return BookingSerializerForStaff


class ConfirmBookingAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = BookingSerializerForStaff

    def post(self, request, pk):
        try:
            booking = AmenityBooking.objects.get(id=pk)
        except AmenityBooking.DoesNotExist:
            raise StandardAPIException(
                code="booking_not_found",
                detail="Booking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if booking.status != BookingStatus.PENDING.value:
            raise StandardAPIException(
                code="invalid_booking_status",
                detail=f"Cannot confirm {booking.status} booking",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking.confirm_booking(
                confirmed_by=(
                    request.user.helixstaff
                    if hasattr(request.user, "helixstaff")
                    else None
                )
            )
        except Exception as e:
            raise StandardAPIException(
                code="confirmation_error",
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return StandardAPIResponse(
            data=self.get_serializer(booking).data, status=status.HTTP_200_OK
        )


class RejectBookingAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = BookingSerializerForStaff

    def post(self, request, pk):
        try:
            booking = AmenityBooking.objects.get(id=pk)
        except AmenityBooking.DoesNotExist:
            raise StandardAPIException(
                code="booking_not_found",
                detail="Booking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if booking.status != BookingStatus.PENDING.value:
            raise StandardAPIException(
                code="invalid_booking_status",
                detail=f"Cannot reject {booking.status} booking",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("rejection_reason")
        remarks = request.data.get("rejection_remarks", "")

        if not reason:
            raise StandardAPIException(
                code="missing_required_param",
                detail="rejection_reason is required",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking.reject_booking(
                reason,
                remarks,
                rejected_by=(
                    request.user.helixstaff
                    if hasattr(request.user, "helixstaff")
                    else None
                ),
            )
        except Exception as e:
            raise StandardAPIException(
                code="rejection_error",
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return StandardAPIResponse(
            data=self.get_serializer(booking).data, status=status.HTTP_200_OK
        )


class CancelBookingAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = BookingSerializerForStaff

    def post(self, request, pk):
        try:
            booking = AmenityBooking.objects.get(id=pk)
        except AmenityBooking.DoesNotExist:
            raise StandardAPIException(
                code="booking_not_found",
                detail="Booking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if is_resident_request(request) and booking.tenant != request.user.resident:
            raise StandardAPIException(
                code="permission_denied",
                detail="Cannot cancel other tenant's booking",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        reason = request.data.get("reason", "")

        try:
            booking.cancel_booking(reason)
        except Exception as e:
            raise StandardAPIException(
                code="cancellation_error",
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if is_resident_request(request):
            serializer_class = BookingSerializerForTenant
        else:
            serializer_class = BookingSerializerForStaff

        return StandardAPIResponse(
            data=serializer_class(booking).data, status=status.HTTP_200_OK
        )


class DuplicateBookingAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = BookingSerializerForTenant

    def post(self, request, pk):
        try:
            original_booking = AmenityBooking.objects.get(id=pk)
        except AmenityBooking.DoesNotExist:
            raise StandardAPIException(
                code="booking_not_found",
                detail="Booking not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if (
            is_resident_request(request)
            and original_booking.tenant != request.user.resident
        ):
            raise StandardAPIException(
                code="permission_denied",
                detail="Cannot duplicate other tenant's booking",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        new_booking_date = request.data.get("booking_date")
        new_start_time = request.data.get("start_time")
        new_end_time = request.data.get("end_time")

        try:
            manager = DuplicateBookingManager(original_booking)
            duplicate_booking = manager.duplicate(
                new_booking_date=new_booking_date,
                new_start_time=new_start_time,
                new_end_time=new_end_time,
            )

            if is_resident_request(request):
                serializer_class = BookingSerializerForTenant
            else:
                serializer_class = BookingSerializerForStaff

            return StandardAPIResponse(
                data=serializer_class(duplicate_booking).data,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            raise StandardAPIException(
                code="duplication_error",
                detail=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class AmenitiesAndReservationsCountAPIView(generics.GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    serializer_class = AmenitiesAndReservationsSummarySerializer

    def get(self, request):
        from locations.models import Amenity

        if is_resident_request(request):
            # For residents: filter amenities and blackout periods by all() since they're shared resources
            # but filter bookings to only show their own
            amenities_count = Amenity.objects.all().count()
            bookings_count = AmenityBooking.objects.filter(
                tenant=request.user.resident
            ).count()
            blackout_periods_count = AmenityBlackoutPeriod.objects.all().count()
        else:
            # For staff: use for_current_user() which filters by access level and location
            amenities_count = Amenity.objects.for_current_user().count()
            bookings_count = AmenityBooking.objects.for_current_user().count()
            blackout_periods_count = (
                AmenityBlackoutPeriod.objects.for_current_user().count()
            )

        data = {
            "amenities_count": amenities_count,
            "bookings_count": bookings_count,
            "blackout_periods_count": blackout_periods_count,
        }

        serializer = self.get_serializer(data)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)
