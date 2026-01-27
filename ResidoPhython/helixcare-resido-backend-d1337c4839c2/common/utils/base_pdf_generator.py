from abc import ABC, abstractmethod
from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class PDFGeneratorContext:
    def __init__(self, model_instance):
        self.instance = model_instance

    def get_instance(self):
        return self.instance


class BasePDFGenerator(ABC):
    def __init__(self, context: PDFGeneratorContext):
        self.context = context
        self.instance = context.get_instance()

    @abstractmethod
    def get_template_name(self) -> str:
        pass

    @abstractmethod
    def prepare_context(self) -> dict:
        pass

    def generate(self) -> BytesIO:
        try:
            # Prepare context data for template
            context_data = self.prepare_context()

            # Render HTML from template
            template_name = self.get_template_name()
            html_string = render_to_string(template_name, context_data)

            # Convert HTML to PDF using weasyprint
            pdf_buffer = self._html_to_pdf(html_string)

            logger.info(
                f"Successfully generated PDF for {self.instance.__class__.__name__} {self.instance.id}"
            )

            return pdf_buffer

        except Exception as e:
            error_msg = (
                f"Error generating PDF for {self.instance.__class__.__name__} "
                f"{self.instance.id}: {str(e)}"
            )
            import traceback

            traceback.print_exc()
            logger.error(error_msg, exc_info=True)
            raise

    def _html_to_pdf(self, html_string: str) -> BytesIO:
        try:
            html_obj = HTML(string=html_string)
            pdf_buffer = BytesIO()
            html_obj.write_pdf(pdf_buffer)

            pdf_buffer.seek(0)
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {str(e)}", exc_info=True)
            raise

    # Common utility methods

    def format_money(self, amount: Any, default: str = "N/A") -> str:
        """
        Format a MoneyField amount or numeric value as currency string.

        Args:
            amount: MoneyField object or numeric value
            default: Default value if amount is None/empty

        Returns:
            Formatted currency string (e.g., "$1,234.56")
        """
        if amount is None:
            return default

        # Handle MoneyField objects
        if hasattr(amount, "amount"):
            amount_value = amount.amount
        else:
            amount_value = amount

        if amount_value is None:
            return default

        try:
            return f"${float(amount_value):,.2f}"
        except (ValueError, TypeError):
            return default

    def get_display_value(
        self, instance: Any, field_name: str, default: str = "N/A"
    ) -> str:
        """
        Get the display value for a choice field or regular field.

        Args:
            instance: Model instance
            field_name: Name of the field
            default: Default value if field is None/empty

        Returns:
            Display value or field value
        """
        if not hasattr(instance, field_name):
            return default

        field_value = getattr(instance, field_name, None)
        if field_value is None:
            return default

        # Try to get display method (e.g., get_status_display())
        display_method = f"get_{field_name}_display"
        if hasattr(instance, display_method):
            try:
                return getattr(instance, display_method)() or default
            except Exception:
                pass

        return str(field_value) if field_value else default

    def safe_get_attr(self, instance: Any, attr_path: str, default: Any = "N/A") -> Any:
        """
        Safely get nested attribute value (e.g., "unit.floor.building.name").

        Args:
            instance: Starting instance
            attr_path: Dot-separated attribute path
            default: Default value if any part of path is None

        Returns:
            Attribute value or default
        """
        try:
            value = instance
            for attr in attr_path.split("."):
                if value is None:
                    return default
                value = getattr(value, attr, None)
            return value if value is not None else default
        except (AttributeError, Exception) as e:
            logger.warning(f"Error getting attribute path '{attr_path}': {str(e)}")
            return default

    def format_date(
        self, date_value: Any, format_str: str = "%B %d, %Y", default: str = "N/A"
    ) -> str:
        """
        Format a date value as string.

        Args:
            date_value: Date/datetime object
            format_str: Date format string
            default: Default value if date is None

        Returns:
            Formatted date string
        """
        if date_value is None:
            return default
        try:
            return date_value.strftime(format_str)
        except (AttributeError, ValueError):
            return default

    def get_location_info(self, unit: Any) -> dict:
        """
        Extract location information from a unit object.

        Args:
            unit: Unit model instance

        Returns:
            Dictionary with location_name, location_address, building_name, floor_number
        """
        location_name = "N/A"
        location_address = "N/A"
        building_name = "N/A"
        floor_number = "N/A"

        try:
            if unit and hasattr(unit, "floor"):
                floor = unit.floor
                if floor:
                    floor_number = floor.floor_number or "N/A"

                    if hasattr(floor, "building"):
                        building = floor.building
                        if building:
                            building_name = building.name or "N/A"

                            if hasattr(building, "location"):
                                location = building.location
                                if location:
                                    location_name = location.name or "N/A"

                                    # Build address
                                    if hasattr(location, "address"):
                                        address_parts = []
                                        if location.address:
                                            address_parts.append(location.address)
                                        if hasattr(location, "city") and location.city:
                                            address_parts.append(location.city)
                                        if (
                                            hasattr(location, "state")
                                            and location.state
                                        ):
                                            address_parts.append(location.state)
                                        if (
                                            hasattr(location, "zipcode")
                                            and location.zipcode
                                        ):
                                            address_parts.append(location.zipcode)
                                        location_address = (
                                            ", ".join(address_parts)
                                            if address_parts
                                            else "N/A"
                                        )
        except Exception as e:
            logger.warning(f"Error getting location info: {str(e)}")

        return {
            "location_name": location_name,
            "location_address": location_address,
            "building_name": building_name,
            "floor_number": floor_number,
        }

    def get_related_objects_list(
        self,
        instance: Any,
        related_name: str,
        display_attr: str = "name",
        limit: Optional[int] = None,
    ) -> list:
        """
        Get list of related objects and extract display attribute.

        Args:
            instance: Model instance
            related_name: Related manager name (e.g., 'pet_policies')
            display_attr: Attribute to extract from each related object
            limit: Optional limit on number of objects

        Returns:
            List of display attribute values
        """
        try:
            if not hasattr(instance, related_name):
                return []

            related_manager = getattr(instance, related_name)
            if not hasattr(related_manager, "all"):
                return []

            queryset = related_manager.all()
            if limit:
                queryset = queryset[:limit]

            return [getattr(obj, display_attr, str(obj)) for obj in queryset]
        except Exception as e:
            logger.warning(f"Error getting related objects '{related_name}': {str(e)}")
            return []

    def join_list(
        self, items: list, separator: str = ", ", default: str = "None"
    ) -> str:
        """
        Join a list of items with separator, returning default if empty.

        Args:
            items: List of items to join
            separator: Separator string
            default: Default value if list is empty

        Returns:
            Joined string or default
        """
        if not items:
            return default
        return separator.join(str(item) for item in items if item)
