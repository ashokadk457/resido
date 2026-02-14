from common.thread_locals import get_current_user
from staff.constants import HELIX_STAFF_FIELD_TO_ACCESS_LEVEL_MAP
from helixauth.constants import AccessLevel


class RLAManagerMixin:
    """
    To be inherited by model managers for filtering queryset based on current
    user's access. Set attribute `path_to_location` to model's relation to location.
    """

    def _for_current_patient(self, user, queryset):
        path_to_resident_id = getattr(self.model._meta, "path_to_resident_id", None)
        if not path_to_resident_id:
            raise NotImplementedError(
                f"RLA not implemented properly for model {self.model.__name__}"
            )

        from helixauth.managers.user.generic import HelixUserManager

        patient = HelixUserManager(user_id=str(user.id))._get_associated_patient()
        if patient is None:
            return queryset.none()

        return queryset.filter(**{path_to_resident_id: str(patient.id)})

    def _for_current_staff(self, user, queryset):
        path_to_location = getattr(self.model._meta, "path_to_location", None)
        if not path_to_location:
            return queryset

        staff = getattr(user, "helixuser_staff", None)
        if not staff:
            return queryset

        access_level = (
            user.access_level
            if user and user.access_level
            else AccessLevel.Location.value
        )
        if access_level == AccessLevel.Admin.value:
            return self.all()
        staff_field_name = HELIX_STAFF_FIELD_TO_ACCESS_LEVEL_MAP.get(access_level)
        if not staff_field_name:
            return self.none()
        staff_field = getattr(staff, staff_field_name)
        staff_field_data = staff_field.all()
        return queryset.filter(
            **self.get_queryset_filter(
                path_to_location=path_to_location,
                access_level=access_level,
                value=staff_field_data,
            )
        )

    def for_current_user(self):
        user, queryset = get_current_user(), self.all()
        if user is None or user.__class__.__name__ != "HelixUser":
            return queryset

        is_staff_user = getattr(user, "is_staff", False)
        if is_staff_user:
            return self._for_current_staff(user=user, queryset=queryset)

        return self._for_current_patient(user=user, queryset=queryset)

    @staticmethod
    def get_queryset_filter(path_to_location, access_level, value):
        obj = {}
        path_to_locations = []
        if isinstance(path_to_location, str):
            path_to_locations = [path_to_location]
        elif isinstance(path_to_location, list):
            path_to_locations = path_to_location
        for i in path_to_locations:
            if access_level == AccessLevel.Location.value:
                obj[path_to_location + "__in"] = value
            elif access_level == AccessLevel.Property.value:
                obj[path_to_location + "__property__in"] = value
            elif access_level == AccessLevel.Customer.value:
                obj[path_to_location + "__property__customer__in"] = value
            elif access_level == AccessLevel.Building.value:
                obj[path_to_location + "__building__in"] = value
            elif access_level == AccessLevel.Floor.value:
                obj[path_to_location + "__building__floor__in"] = value
            elif access_level == AccessLevel.Unit.value:
                obj[path_to_location + "__building__floor__unit__in"] = value
        return obj
