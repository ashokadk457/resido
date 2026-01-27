import logging
from common.utils.base_pdf_generator import BasePDFGenerator, PDFGeneratorContext

logger = logging.getLogger(__name__)


class LeasePDFGenerator(BasePDFGenerator):
    """PDF generator for Lease model."""

    def __init__(self, lease_instance):
        """
        Initialize with a lease instance.

        Args:
            lease_instance: Lease model instance
        """
        context = PDFGeneratorContext(lease_instance)
        super().__init__(context)
        self.lease = lease_instance

    def get_template_name(self) -> str:
        """Get the template name for lease PDF."""
        return "lease/lease_pdf.html"

    def prepare_context(self) -> dict:
        """Prepare context data for the HTML template."""

        # Get additional occupants
        additional_occupants = []
        if hasattr(self.lease, "other_occupants"):
            try:
                for occupant in self.lease.other_occupants.all()[:3]:
                    additional_occupants.append(
                        {
                            "name": self.safe_get_attr(occupant, "name", "N/A"),
                            "age": str(self.safe_get_attr(occupant, "age", "N/A")),
                            "relationship": self.safe_get_attr(
                                occupant, "relationship", "N/A"
                            ),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error getting additional occupants: {str(e)}")

        # Get utilities
        utilities = []
        if hasattr(self.lease, "utility_services"):
            try:
                for util in self.lease.utility_services.all():
                    service_display = self.get_display_value(
                        util,
                        "service",
                        util.service if hasattr(util, "service") else "N/A",
                    )
                    responsibility = self.safe_get_attr(
                        util, "responsible", "TENANT"
                    ).upper()
                    utilities.append(
                        {"service": service_display, "responsible": responsibility}
                    )
            except Exception as e:
                logger.warning(f"Error getting utilities: {str(e)}")

        # Default utilities if none exist
        if not utilities:
            utilities = [
                {"service": "Electricity", "responsible": "RENTER"},
                {"service": "Internet", "responsible": "RENTER"},
                {"service": "Phone", "responsible": "RENTER"},
                {"service": "Cable", "responsible": "RENTER"},
                {"service": "Gas", "responsible": "LANDLORD"},
                {"service": "Water", "responsible": "LANDLORD"},
                {"service": "Sewer/Septic", "responsible": "LANDLORD"},
                {"service": "Trash", "responsible": "RENTER"},
                {"service": "Lawn Care", "responsible": "RENTER"},
                {"service": "Snow Removal", "responsible": "RENTER"},
                {"service": "HOA/Condo Fee", "responsible": "LANDLORD"},
            ]

        # Prepare payment methods
        payment_methods = self.join_list(
            self.lease.payments_accepted if self.lease.payments_accepted else [],
            default="Cash, Check, Bank Transfer",
        )

        # Get parking types
        parking_types = self.join_list(
            self.lease.parking_available if self.lease.parking_available else [],
            default="Not Available",
        )

        # Get location info from unit
        location_info = {}
        if self.lease.unit:
            location_info = self.get_location_info(self.lease.unit)

        context = {
            "landlord_name": self._get_landlord_name(),
            "tenant_name": self._get_primary_tenant_name(),
            "tenant_email": self._get_tenant_email(),
            "tenant_phone": self._get_tenant_phone(),
            "lease_start_date": self.format_date(self.lease.start_date, default="N/A"),
            "lease_end_date": self.format_date(self.lease.end_date, default="N/A"),
            "lease_term": self.get_display_value(self.lease, "lease_term"),
            "property_address": location_info.get(
                "location_address", self._get_property_address_fallback()
            ),
            "property_name": location_info.get(
                "location_name", self._get_property_name_fallback()
            ),
            "building_name": location_info.get(
                "building_name", self._get_building_name_fallback()
            ),
            "unit_number": self.safe_get_attr(self.lease, "unit.unit_number", "N/A"),
            "rent_amount": self.lease.rent_amount or 0.0,
            "rent_total": (self.lease.rent_amount or 0.0)
            + 100.0,  # Base + additional rent
            "prorated_rent_amount": self.lease.prorated_rent_amount or 0.0,
            "security_amount": self.lease.security_amount or 0.0,
            "security_refundable": self.lease.security_refundable,
            "pet_deposit_amount": self.lease.pet_deposit_amount or 0.0,
            "pet_deposit_refundable": self.lease.pet_deposit_refundable,
            "total_deposits": self._get_total_deposits(),
            "one_time_fees_amount": self.lease.one_time_fees_amount or 0.0,
            "payment_methods": payment_methods,
            "smoking_allowed": self.lease.smoking_allowed,
            "parking_available": bool(self.lease.parking_available),
            "parking_types": parking_types,
            "landlord_email": self.lease.landlord_email or "N/A",
            "landlord_phone": self.lease.landlord_phone or "N/A",
            "landlord_address": self.lease.landlord_address or "N/A",
            "additional_occupants": additional_occupants,
            "utilities": utilities,
            "early_termination_allowed": self.lease.early_termination_allowed,
            "logo_url": "",  #  Resido logo URL
        }

        return context

    def _get_landlord_name(self):
        """Get landlord name."""
        first_name = self.lease.landlord_first_name or ""
        last_name = self.lease.landlord_last_name or ""
        name = f"{first_name} {last_name}".strip()
        return name if name else "Landlord Name"

    def _get_primary_tenant_name(self):
        """Get primary tenant name."""
        first_name = self.safe_get_attr(self.lease, "resident.user.first_name", "")
        last_name = self.safe_get_attr(self.lease, "resident.user.last_name", "")
        if first_name or last_name:
            return f"{first_name} {last_name}".strip()
        return "Tenant Name"

    def _get_tenant_email(self):
        """Get tenant email."""
        return self.safe_get_attr(self.lease, "resident.user.email", "N/A")

    def _get_tenant_phone(self):
        """Get tenant phone."""
        return self.safe_get_attr(self.lease, "resident.user.phone", "N/A")

    def _get_property_address_fallback(self):
        """Get property address from lease (fallback method)."""
        try:
            location = self.safe_get_attr(
                self.lease, "unit.floor.building.location_detail"
            )
            if location and location != "N/A":
                address_parts = []
                if hasattr(location, "address") and location.address:
                    address_parts.append(location.address)
                if hasattr(location, "city") and location.city:
                    address_parts.append(location.city)
                if hasattr(location, "state") and location.state:
                    address_parts.append(location.state)
                if hasattr(location, "zipcode") and location.zipcode:
                    address_parts.append(location.zipcode)
                return ", ".join(address_parts) if address_parts else "N/A"
        except Exception as e:
            logger.warning(f"Error getting property address: {str(e)}")
        return "N/A"

    def _get_property_name_fallback(self):
        """Get property/location name (fallback method)."""
        return self.safe_get_attr(
            self.lease, "unit.floor.building.location_detail.name", "N/A"
        )

    def _get_building_name_fallback(self):
        """Get building name (fallback method)."""
        return self.safe_get_attr(self.lease, "unit.floor.building.name", "N/A")

    def _get_total_deposits(self):
        """Get total deposits (security + pet deposit)."""
        total = (self.lease.security_amount or 0) + (self.lease.pet_deposit_amount or 0)
        return total
