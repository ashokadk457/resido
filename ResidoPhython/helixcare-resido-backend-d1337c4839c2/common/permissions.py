from rest_framework.permissions import BasePermission, AllowAny

from helixauth.mixins.permission import HelixPermissionMixin
from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedResidentPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request=request, view=view):
            return False

        if hasattr(request, "is_resident") and not getattr(request, "is_resident"):
            return False

        allowed_methods_set = getattr(view, "allowed_methods_to_resident", None)

        # if methods allowed are not defined
        # we assume all are allowed to patient
        if not allowed_methods_set:
            return True

        httpmethod = request.method.lower()
        return allowed_methods_set.get(httpmethod, False)


class IsAuthenticatedHelixUser(BasePermission):
    def has_permission(self, request, view):
        return (
            not request.user.is_anonymous
            and hasattr(request, "is_helix_user")
            and getattr(request, "is_helix_user")
        )


class HelixUserBasePermission(BasePermission, HelixPermissionMixin):
    message = "You do not have permission to perform this action"

    def has_permission(self, request, view):
        is_authenticated = IsAuthenticatedHelixUser().has_permission(request, view)
        if not is_authenticated:
            return False
        entity = getattr(view, "entity", None)
        submodule = getattr(view, "submodule", None)
        httpmethod = request.method.lower()
        return True
        roles = (
            request.staff.user_roles.all()
            if request.user.__class__.__name__ == "HelixUser"
            and hasattr(request, "is_helix_user")
            and getattr(request, "is_helix_user")
            else None
        )
        modules = None
        if not entity:
            return True  # this check is to be removed once all apps are integrated
        if not roles or not entity:
            return False
        if submodule:
            modules = self.get_entity_module_having_submodule(
                entity=entity, code=submodule
            )
        allowed, _ = self.check_method_permission_of_entity_for_role(
            httpmethod=httpmethod,
            entity=entity,
            roles=roles,
            modules=modules,
            submodule=submodule,
        )
        return allowed

    def has_object_permission(self, request, view, obj):
        return True


class AppointmentListCreatePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return True

        return HelixUserBasePermission().has_permission(
            request, view
        ) | IsAuthenticatedResidentPermission().has_permission(request, view)


class IsCustomerOnboardingUser(IsAuthenticated):
    def has_permission(self, request, view):
        if not super(IsCustomerOnboardingUser, self).has_permission(request, view):
            return False

        return request.user.email == request.data.get("admin", {}).get("email")


class AllowAnyOrIsAuthenticatedPatient(BasePermission):
    def has_permission(self, request, view):
        return AllowAny().has_permission(
            request, view
        ) or IsAuthenticatedResidentPermission().has_permission(request, view)
