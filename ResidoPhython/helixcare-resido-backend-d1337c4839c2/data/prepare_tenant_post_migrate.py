import yaml
import pandas as pd
from helixauth.models import Module, ModulePermission, UserRole
from helixauth.managers.permissions import SubModulePermissionManager
from helixauth.managers.composition import (
    ModuleCompositionManager,
    SubModuleCompositionManager,
)


def populate_user_roles(apps=None):
    if not apps:
        from django.apps import apps

    UserRole = apps.get_model("helixauth", "UserRole")
    UserGroup = None
    try:
        UserGroup = apps.get_model("helixauth", "UserGroup")
    except Exception as e:
        print(f"Exception while loading UserGroup model: {e}")
        pass

    group_obj = None
    if UserGroup:
        group_obj, _ = UserGroup.objects.get_or_create(name="General")

    df = pd.read_csv("data/user_roles.csv")
    for _, row in df.iterrows():
        role_code = row["role_name"]

        # Check if the UserRole already exists
        existing_role = UserRole.objects.filter(role_name=role_code).last()

        is_role_active = row["is_role_active"]
        seeded = row["seeded"]

        is_seeded = True if seeded == "Y" else False
        is_active = True if is_role_active == "Y" else False

        if existing_role:
            # UserRole already exists, update the existing role
            existing_role.role_name = row["role_name"]
            existing_role.description = row["description"]
            existing_role.is_role_active = is_active
            existing_role.seeded = is_seeded
            if not existing_role.group:
                existing_role.group = group_obj
            existing_role.save()
        else:
            UserRole.objects.create(
                role_name=row["role_name"],
                description=row["description"],
                is_role_active=is_active,
                seeded=is_seeded,
                group=group_obj,
            )


def populate_modules():
    df = pd.read_csv("data/modules.csv")
    for _, row in df.iterrows():
        module_code = row["code"]

        # Check if the Module already exists
        existing_module = Module.objects.filter(code=module_code).last()
        is_active = row["is_active"]
        is_module_active = True if is_active == "Y" else False

        if existing_module:
            # Module already exists, update the existing module
            existing_module.product = row["product"]
            existing_module.name = row["name"]
            existing_module.description = row["description"]
            existing_module.is_active = is_module_active
            existing_module.save()
        else:
            Module.objects.create(
                product=row["product"],
                code=module_code,
                name=row["name"],
                description=row["description"],
                is_active=is_module_active,
            )


def populate_module_permissions():
    role_map = {}
    df = pd.read_csv("data/user_roles.csv")
    for _, row in df.iterrows():
        role_name = row["role_name"]
        role_code = row["code"]
        role_map[role_code] = role_name
    df = pd.read_csv("data/permissions/modules_permissions_mapping.csv")
    for _, row in df.iterrows():
        module_code = row.iloc[0]
        module = Module.objects.filter(code__iexact=module_code).last()

        if not module:
            print(f"Module not found for code: {module_code}, skipping...")
            continue

        # Iterate through permissions for each role
        for role_code, permission in zip(df.columns[2:], row[2:]):
            role_name = role_map.get(role_code)
            role = UserRole.objects.filter(role_name=role_name).last()

            if not role:
                print(f"Role not found for code: {role_code}, skipping...")
                continue

            permission_str = str(permission).lower()

            can_create = True if "c" in permission_str else False
            can_view = True if "r" in permission_str else False
            can_update = True if "u" in permission_str else False
            can_delete = True if "d" in permission_str else False

            if "n" in permission_str:
                can_create = can_view = can_update = can_delete = False

            print(
                module.code,
                role.role_name,
                permission,
                can_create,
                can_view,
                can_update,
                can_delete,
            )

            # Check if the permission already exists
            existing_permission = ModulePermission.objects.filter(
                module=module, role=role
            ).last()

            if existing_permission:
                # Permission already exists, update the existing permission
                existing_permission.can_create = can_create
                existing_permission.can_view = can_view
                existing_permission.can_update = can_update
                existing_permission.can_delete = can_delete
                existing_permission.is_active = True
                existing_permission.save()
            else:
                # Permission does not exist, create a new permission
                ModulePermission.objects.create(
                    module=module,
                    role=role,
                    can_create=can_create,
                    can_view=can_view,
                    can_update=can_update,
                    can_delete=can_delete,
                    is_active=True,
                )


def populate_module_compositions():
    module_object_map = {}
    for obj in Module.objects.all():
        module_object_map[obj.code] = obj
    with open("data/permissions/modules_composition.yaml", "r") as yaml_file:
        file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
        for data in file_data:
            module = module_object_map[data["module"]]
            data["module"] = module
            ModuleCompositionManager.model.objects.get_or_create(
                module=module, entity=data["entity"], defaults=data
            )


def populate_submodule_and_compositions():
    all_roles = UserRole.objects.all()
    role_object_map = {role.role_name: role for role in all_roles}
    module_object_map = {}
    for obj in Module.objects.all():
        module_object_map[obj.code] = obj
    submodule_object_map = {}
    with open("data/permissions/submodules.yaml", "r") as yaml_file:
        file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
        for data in file_data:
            module = module_object_map[data["module"]]
            data["module"] = module
            obj, _ = SubModuleCompositionManager.model.objects.get_or_create(
                module=module, submodule=data["submodule"], defaults=data
            )
            submodule_object_map[data["code"]] = obj

    with open("data/permissions/submodules_permissions.yaml", "r") as yaml_file:
        file_data = yaml.load_all(yaml_file, yaml.BaseLoader)
        for data in file_data:
            submodule = submodule_object_map[data["submodule"]]
            role = role_object_map[data["role"]]
            data["submodule"] = submodule
            data["role"] = role
            SubModulePermissionManager.model.objects.get_or_create(
                submodule=submodule, role=role, defaults=data
            )
