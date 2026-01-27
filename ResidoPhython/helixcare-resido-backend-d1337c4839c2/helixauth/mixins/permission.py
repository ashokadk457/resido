from helixauth.managers.composition import (
    ModuleCompositionManager,
    SubModuleCompositionManager,
)
from helixauth.managers.permissions import (
    ModulePermissionManager,
    SubModulePermissionManager,
)


class HelixPermissionMixin:
    HTTPMETHOD_PERM_MAP = {
        "get": "can_view",
        "put": "can_update",
        "patch": "can_update",
        "delete": "can_delete",
        "post": "can_create",
    }

    @staticmethod
    def get_entity_modules(entity):
        comp = ModuleCompositionManager.filter_by(entity=entity)
        return [c.module for c in comp]

    @staticmethod
    def get_entity_module_having_submodule(entity, code):
        submodule_objs = SubModuleCompositionManager.filter_by(code=code)
        submod_modules = [m.module for m in submodule_objs]
        comp_objs = ModuleCompositionManager.filter_by(
            entity=entity, module__in=submod_modules
        )
        return [c.module for c in comp_objs]

    @staticmethod
    def get_module_perm_for_role(modules, roles, active=True):
        return ModulePermissionManager.filter_by(
            module__in=modules, role__in=roles, is_active=active
        )

    @classmethod
    def check_method_permission_of_entity_for_role(
        cls, httpmethod, entity, roles, modules=None, submodule=None
    ) -> tuple[bool, chr]:
        if not modules:
            modules = cls.get_entity_modules(entity=entity)
        if not modules:
            return False, "invalid_entity"
        module_perms = cls.get_module_perm_for_role(modules=modules, roles=roles)
        if not module_perms:
            return False, "no_active_perm"
        perm_attr = cls.HTTPMETHOD_PERM_MAP.get(httpmethod.lower())
        for module_perm in module_perms:
            if hasattr(module_perm, perm_attr) and getattr(
                module_perm, perm_attr, False
            ):
                if submodule:
                    allowed, _ = cls.check_submodule_permission_of_module_for_role(
                        modules=module_perm.module,
                        submodule=submodule,
                        roles=roles,
                        perm_attr=perm_attr,
                    )
                    if not allowed:
                        continue
                return True, None
        return False, "not_allowed"

    @staticmethod
    def check_submodule_permission_of_module_for_role(
        module, submodule, roles, perm_attr
    ):
        submodule_obj = SubModuleCompositionManager.filter_by(
            module=module, submodule=submodule
        ).first()
        if not submodule_obj:
            return False, "invalid_submodule"
        submodule_perms = SubModulePermissionManager.filter_by(
            submodule=submodule_obj, role__in=roles, active=True
        )
        if not submodule_perms:
            return False, "no_active_perm"
        for submodule_perm in submodule_perms:
            if hasattr(submodule_perm, perm_attr) and getattr(
                submodule_perm, perm_attr, False
            ):
                return True, None
        return False, "not_allowed"
