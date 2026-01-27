import logging
from common.utils.base_pdf_generator import BasePDFGenerator, PDFGeneratorContext

logger = logging.getLogger(__name__)


class UnitPDFGenerator(BasePDFGenerator):
    """PDF generator for Unit model."""

    def __init__(self, unit_instance):
        """
        Initialize with a unit instance.

        Args:
            unit_instance: Unit model instance
        """
        context = PDFGeneratorContext(unit_instance)
        super().__init__(context)
        self.unit = unit_instance

    def get_template_name(self) -> str:
        """Get the template name for unit PDF."""
        return 'unit/unit_pdf.html'

    def prepare_context(self) -> dict:
        """Prepare context data for the HTML template."""
        
        # Get location details using common utility
        location_info = self.get_location_info(self.unit)

        # Get parking information
        parking_info = []
        if self.unit.parking_slots.exists():
            for slot in self.unit.parking_slots.all():
                zone_name = self.safe_get_attr(slot, 'zone.name', 'N/A')
                parking_info.append(f"{slot.slot_no} ({zone_name})")
        elif self.unit.parking_zone:
            parking_info.append(f"Zone: {self.unit.parking_zone.name}")
        
        parking_details = self.join_list(parking_info, default="Not Available")

        # Get policies using common utility
        pet_policies = self.get_related_objects_list(self.unit, 'pet_policies', 'name')
        pet_policies_str = self.join_list(pet_policies)

        violation_policies = self.get_related_objects_list(self.unit, 'violation_policies', 'name')
        violation_policies_str = self.join_list(violation_policies)

        # Get administration charges
        admin_charges = []
        if self.unit.administration_charges.exists():
            for charge in self.unit.administration_charges.filter(is_active=True):
                charge_amount = charge.charge_amount.amount if charge.charge_amount else 0
                admin_charges.append({
                    'name': charge.charge_name,
                    'amount': charge_amount
                })

        context = {
            'unit_number': self.unit.unit_number or "N/A",
            'display_id': self.unit.display_id or "N/A",
            'unit_type': self.get_display_value(self.unit, 'unit_type'),
            'status': self.get_display_value(self.unit, 'status'),
            'location_name': location_info['location_name'],
            'location_address': location_info['location_address'],
            'building_name': location_info['building_name'],
            'floor_number': location_info['floor_number'],
            'unit_size': f"{self.unit.unit_size} sq ft" if self.unit.unit_size else "N/A",
            'floor_plan': self.unit.floor_plan or "N/A",
            'is_furnished': self.unit.is_furnished,
            'furnished_price': self.format_money(self.unit.furnished_price),
            'unfurnished_price': self.format_money(self.unit.unfurnished_price),
            'furnished_security_deposit': self.format_money(self.unit.furnished_security_deposit),
            'unfurnished_security_deposit': self.format_money(self.unit.unfurnished_security_deposit),
            'deposit_refundable': self.unit.deposit_refundable,
            'unit_capacity': self.unit.unit_capacity or "N/A",
            'max_unit_capacity': self.unit.max_unit_capacity or "N/A",
            'exceeding_occupancy_fee': self.format_money(self.unit.exceeding_occupancy_fee),
            'hoa_fee': self.format_money(self.unit.hoa_fee),
            'ownership': self.unit.ownership or "N/A",
            'smoking_status': self.get_display_value(self.unit, 'smoking_status'),
            'allow_smoking': self.unit.allow_smoking,
            'parking_details': parking_details,
            'parking_type': self.get_display_value(self.unit, 'parking_type'),
            'parking_included_in_rent': self.unit.parking_included_in_rent,
            'additional_parking_cost': self.format_money(self.unit.additional_parking_cost),
            'no_of_spaces_per_unit': self.unit.no_of_spaces_per_unit or "N/A",
            'guest_parking_available': self.unit.guest_parking_available,
            'accessible_parking_available': self.unit.accessible_parking_available,
            'is_pet_allowed': self.unit.is_pet_allowed,
            'is_service_animal_allowed': self.unit.is_service_animal_allowed,
            'pet_type': self.unit.pet_type or "N/A",
            'pet_species': self.unit.pet_species or "N/A",
            'max_pets': self.unit.max_pets or "N/A",
            'pet_fees_type': self.unit.pet_fees_type or "N/A",
            'pet_fees_amount': self.format_money(self.unit.pet_fees_amount),
            'pet_security_deposit_amount': self.format_money(self.unit.pet_security_deposit_amount),
            'pet_security_deposit_refundable': self.unit.pet_security_deposit_refundable,
            'pet_policies': pet_policies_str,
            'violation_policies': violation_policies_str,
            'admin_charges_applicable': self.unit.admin_charges_applicable,
            'administration_charges': admin_charges,
            'is_active': self.unit.is_active,
            'created_on': self.format_date(self.unit.created_on),
        }

        return context

