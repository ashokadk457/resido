from functools import lru_cache
from rest_framework.permissions import AllowAny


class AttributeLevelPermissionMixin:
    @staticmethod
    @lru_cache(maxsize=512)
    def _get_entity(app_name, entity):
        from helixauth.models import Entity

        return Entity.objects.filter_from_cache(app_name=app_name, entity=entity)

    @staticmethod
    def _get_entity_attribute_composition(entity_obj, resp_attrs):
        from helixauth.models import EntityAttributeComposition

        return EntityAttributeComposition.objects.filter_from_cache(
            entity_id=str(entity_obj["id"]), attribute__in=resp_attrs
        )

    @staticmethod
    def _get_entity_attribute_permission(roles, entity_attrs):
        from helixauth.models import EntityAttributePermission

        role_ids = [str(r.id) for r in roles]
        entity_attrs_ids = [str(e["id"]) for e in entity_attrs]
        return EntityAttributePermission.objects.filter(
            attribute__in=entity_attrs_ids, role__in=role_ids
        ).select_related("attribute")

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        model = getattr(self.Meta, "model")
        if not model:
            return resp
        request_obj = self.context.get("request")
        if (
            not request_obj
            or not hasattr(request_obj, "user")
            or (
                hasattr(request_obj, "is_resident")
                and getattr(request_obj, "is_resident") is True
            )
            or request_obj.user.__class__.__name__ == "AnonymousUser"
        ):
            return resp
        if self.context.get("view") and hasattr(
            self.context.get("view"), "permission_classes"
        ):
            permissions = getattr(self.context.get("view"), "permission_classes")
            for perm in permissions:
                if perm == AllowAny:
                    return resp
        app_name = getattr(getattr(model, "_meta"), "app_label")
        entity = model.__name__
        entity_obj = self._get_entity(app_name=app_name, entity=entity)
        if len(entity_obj) == 0:
            return resp
        entity_obj = entity_obj[0]
        resp_attrs = list(resp.keys())
        entity_attrs = self._get_entity_attribute_composition(
            entity_obj=entity_obj, resp_attrs=resp_attrs
        )
        if len(entity_attrs) == 0:
            return resp

        roles = self.context["request"].user.helixuser_staff.user_roles.filter(
            is_role_active=True
        )
        attrs_permission = self._get_entity_attribute_permission(
            roles=roles, entity_attrs=entity_attrs
        )
        for attr in attrs_permission:
            if not attr.has_perm:
                field_name = attr.attribute.attribute
                if hasattr(resp, field_name):
                    attr_val = getattr(resp, field_name)
                    if not isinstance(attr_val, list) and not isinstance(
                        attr_val, dict
                    ):
                        resp[field_name] = "********"
                elif resp.get(field_name):
                    attr_val = resp.get(field_name)
                    if not isinstance(attr_val, list) and not isinstance(
                        attr_val, dict
                    ):
                        resp[field_name] = "********"

        return resp
