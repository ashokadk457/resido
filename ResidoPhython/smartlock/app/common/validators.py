import re

from rest_framework import serializers
from common.errors import ERROR_DETAILS


def normalize_empty_to_none(value):
    """
    Convert empty strings or whitespace-only strings to None.
    This is useful for optional fields to avoid unique constraint violations.

    Args:
        value: The value to normalize

    Returns:
        None if value is empty/whitespace, otherwise returns the original value
    """
    if not value or (isinstance(value, str) and value.strip() == ""):
        return None
    return value


def validate_not_whitespace(value, field_name):
    """
    Validate that a field is not empty or just whitespace.

    Args:
        value: The value to validate
        field_name: The name of the field (for error messages)

    Returns:
        Stripped value if valid

    Raises:
        ValidationError if value is empty or whitespace
    """
    if not value or not value.strip():
        error_code = f"{field_name}_required"
        error_message = ERROR_DETAILS.get(
            error_code, f"{field_name.replace('_', ' ').title()} is required"
        )
        raise serializers.ValidationError(
            code=error_code,
            detail=error_message,
        )
    return value.strip()


def check_unique_field(
    model_class, field_name, value, exclude_instance=None, case_insensitive=False
):
    """
    Check if a field value is unique in the database.

    Args:
        model_class: The Django model class to check
        field_name: The name of the field to check uniqueness for
        value: The value to check
        exclude_instance: Optional instance to exclude from the check (for updates)
        case_insensitive: Whether to perform case-insensitive comparison

    Returns:
        The value if unique

    Raises:
        ValidationError if value already exists
    """
    if not value:
        return value

    # Build the query
    lookup = f"{field_name}__iexact" if case_insensitive else field_name
    queryset = model_class.objects.filter(**{lookup: value})

    # Exclude current instance during updates
    if exclude_instance is not None:
        queryset = queryset.exclude(pk=exclude_instance.pk)

    if queryset.exists():
        error_code = f"{field_name}_already_exists"
        error_message = ERROR_DETAILS.get(
            error_code, f"{field_name.replace('_', ' ').title()} already exists"
        )
        raise serializers.ValidationError(
            code=error_code,
            detail=error_message,
        )

    return value


def validate_phone_number(value: str):
    """
    Validate that the phone number:
    1. Is not all zeros
    2. Matches a basic international phone pattern (+optional, 7–15 digits)
    """
    if not value:
        return value

    cleaned = value.replace(" ", "").replace("-", "")

    # Check: not all zeros
    if re.fullmatch(r"0+", cleaned):
        raise serializers.ValidationError(
            code="all_zero_phone_number",
            detail=ERROR_DETAILS["all_zero_phone_number"].format(param="phone"),
        )

    # Check: valid phone number pattern
    if not re.fullmatch(r"^\+?[1-9]\d{6,14}$", cleaned):
        raise serializers.ValidationError(
            code="invalid_phone_format",
            detail=ERROR_DETAILS["invalid_phone_format"].format(param="phone"),
        )

    return value


def validate_country_code(value: str):
    """
    Validate that the country code:
    1. Starts with + sign
    2. Followed by 1-3 digits

    Valid format: +1, +44, +91, +886, etc.
    """
    if not value:
        return value

    cleaned = value.strip()

    if not re.fullmatch(r"^\+[0-9]{1,3}$", cleaned):
        raise serializers.ValidationError(
            code="invalid_country_code",
            detail=ERROR_DETAILS["invalid_country_code"].format(country_code=value),
        )

    return value


class AgeValidationMixin:
    """
    Mixin to add age field validation with custom error messages.

    Use this in serializers that have an 'age' field to ensure:
    - Age is not negative
    - Age does not exceed 150 years

    Example:
        class MySerializer(AgeValidationMixin, BaseSerializer):
            class Meta:
                model = MyModel
                fields = "__all__"
    """

    def validate_age(self, value):
        """
        Validate age field ensuring it's between 0 and 150.

        Args:
            value: The age value to validate

        Returns:
            The validated age value

        Raises:
            ValidationError: If age is negative or exceeds 150
        """
        if value is not None:
            if value < 0:
                raise serializers.ValidationError(
                    code="negative_age",
                    detail=ERROR_DETAILS["negative_age"],
                )
            if value > 150:
                raise serializers.ValidationError(
                    code="invalid_age_range",
                    detail=ERROR_DETAILS["invalid_age_range"],
                )
        return value
