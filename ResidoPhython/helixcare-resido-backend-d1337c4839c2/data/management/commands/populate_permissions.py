import yaml
from django.apps import apps
from django.db import connection
from django.core.management.base import BaseCommand

from common.utils.logging import logger
from helixauth.managers.module import ModuleManager

# from helixauth.managers.permissions import (
#     ModulePermissionManager,
#     SubModulePermissionManager,
# )
from helixauth.models import (
    Entity,
    EntityAttributeComposition,
    UserRole,
    Module,
    SubModuleComposition,
    ModulePermission,
    SubModulePermission,
    EntityAttributePermission,
)
from helixauth.managers.composition import (
    ModuleCompositionManager,
    #    SubModuleCompositionManager,
)
from data.prepare_tenant_post_migrate import (
    populate_user_roles,
    #    populate_modules,
    populate_module_permissions,
    #    populate_module_compositions,
    populate_submodule_and_compositions,
)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")

    @staticmethod
    def seed_modules_and_their_compositions():
        module_object_map = {}
        with open("data/permissions/modules.yaml", "r") as yaml_file:
            file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
            for data in file_data:
                obj, _ = ModuleManager.model.objects.get_or_create(
                    code=data["code"], defaults=data
                )
                module_object_map[data["code"]] = obj

        with open("data/permissions/modules_composition.yaml", "r") as yaml_file:
            file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
            for data in file_data:
                module = module_object_map[data["module"]]
                data["module"] = module
                ent, _ = Entity.objects.get_or_create(
                    entity=data["entity"],
                    defaults={
                        "app_name": data.pop("app_name"),
                        "entity": data["entity"],
                    },
                )
                data["entity_obj"] = ent
                ModuleCompositionManager.model.objects.update_or_create(
                    module=module, entity=data["entity"], defaults=data
                )

        SKIPPED_FIELDS = [
            "id",
            "created_on",
            "updated_on",
            "created_by",
            "updated_by",
            "version",
        ]
        for obj in Entity.objects.all():
            try:
                model = apps.get_model(obj.app_name, obj.entity)
                for field in model._meta.get_fields():
                    if field.name not in SKIPPED_FIELDS:
                        EntityAttributeComposition.objects.get_or_create(
                            entity=obj,
                            attribute=field.name,
                            defaults={"entity": obj, "attribute": field.name},
                        )
            except Exception as e:
                logger.warning(f"Exception while seeding entity attributes: {e}")

    def _sync_new_modules_submodules_attributes_to_existing_roles(self):
        """
        Optimized bulk sync of permissions to roles.
        Uses bulk_create with ignore_conflicts for performance.
        """
        all_roles = list(UserRole.objects.all())
        all_modules = list(Module.objects.filter(is_active=True))
        all_subs = list(SubModuleComposition.objects.all())
        all_attrs = list(EntityAttributeComposition.objects.all())

        logger.info(
            f"Syncing permissions: {len(all_roles)} roles, {len(all_modules)} modules, "
            f"{len(all_subs)} submodules, {len(all_attrs)} attributes"
        )

        # Bulk create ModulePermissions
        module_perms = [
            ModulePermission(
                module=mod,
                role=role,
                can_view=False,
                can_create=False,
                can_delete=False,
                can_update=False,
                is_active=True,
            )
            for role in all_roles
            for mod in all_modules
        ]
        if module_perms:
            ModulePermission.objects.bulk_create(
                module_perms, ignore_conflicts=True, batch_size=500
            )
            logger.info(f"ModulePermissions: {len(module_perms)} processed")

        # Bulk create SubModulePermissions
        sub_perms = [
            SubModulePermission(
                submodule=sub,
                role=role,
                can_view=False,
                can_create=False,
                can_delete=False,
                can_update=False,
                is_active=True,
            )
            for role in all_roles
            for sub in all_subs
        ]
        if sub_perms:
            SubModulePermission.objects.bulk_create(
                sub_perms, ignore_conflicts=True, batch_size=500
            )
            logger.info(f"SubModulePermissions: {len(sub_perms)} processed")

        # Bulk create EntityAttributePermissions
        attr_perms = [
            EntityAttributePermission(
                attribute=attr,
                role=role,
                has_perm=True,
            )
            for role in all_roles
            for attr in all_attrs
        ]
        if attr_perms:
            EntityAttributePermission.objects.bulk_create(
                attr_perms, ignore_conflicts=True, batch_size=1000
            )
            logger.info(f"EntityAttributePermissions: {len(attr_perms)} processed")

        logger.info("Permissions sync completed")

    def handle(self, *args, **options):
        if options.get("schema"):
            schema_name = options["schema"]
            connection.set_schema(schema_name)

        self.seed_modules_and_their_compositions()
        populate_user_roles()
        # populate_modules()
        populate_module_permissions()
        # populate_module_compositions()
        populate_submodule_and_compositions()

        self._sync_new_modules_submodules_attributes_to_existing_roles()

        # Reset the schema name to the default after creating the user
        if options.get("schema_name"):
            connection.set_schema_to_public()
