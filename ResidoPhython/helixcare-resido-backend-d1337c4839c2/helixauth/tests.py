from django.urls import reverse
from rest_framework import status

from common.tests import BaseTenantTestCase
from helixauth.models import UserRole, Module, ModuleComposition, ModulePermission


class BaseTestCase(BaseTenantTestCase):
    def create_user_role(self, **kwargs):
        return UserRole.objects.create(**kwargs)

    def create_module(self, **kwargs):
        return Module.objects.create(**kwargs)

    def create_module_composition(self, **kwargs):
        return ModuleComposition.objects.create(**kwargs)

    def create_module_permission(self, **kwargs):
        return ModulePermission.objects.update_or_create(
            module=kwargs.pop("module"), role=kwargs.pop("role"), defaults=kwargs
        )

    def retrieve_object(self, url, pk):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def update_object(self, url, data):
        response = self.client.put(path=url, data=data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response


# class UserRoleListCreateViewTestCase(BaseTestCase):
#     def test_user_role_list_view(self):
#         self.create_user_role(
#             role_name="Test Role",
#             description="Test Description",
#             is_role_active=True,
#             seeded=False,
#         )
#         url = reverse("user_roles")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_user_role(self):
#         data = {
#             "role_name": "New Role",
#             "description": "New Role Description",
#             "is_role_active": True,
#             "seeded": False,
#         }
#
#         url = reverse("user_roles")
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class UserRoleRetrieveUpdateViewTestCase(BaseTestCase):
    def test_retrieve_user_role(self):
        user_role = self.create_user_role(
            role_name="Test Role",
            description="Test Description",
            is_role_active=True,
            seeded=False,
        )
        url = reverse("user_role_detail", kwargs={"pk": user_role.pk})
        self.retrieve_object(url, user_role.pk)

    # def test_update_user_role(self):
    #     user_role = self.create_user_role(
    #         role_name="Test Role 1",
    #         description="Test Description",
    #         is_role_active=True,
    #         seeded=False,
    #     )
    #     updated_data = {
    #         "code": "UPDATED",
    #         "role_name": "Updated Role",
    #         "description": "Updated Role Description",
    #         "is_role_active": False,
    #     }
    #
    #     url = reverse("user_role_detail", kwargs={"pk": user_role.pk})
    #     self.update_object(url, updated_data)
    #
    #     user_role.refresh_from_db()
    #     self.assertEqual(user_role.role_name, "Updated Role")
    #     self.assertEqual(user_role.description, "Updated Role Description")
    #     self.assertEqual(user_role.is_role_active, False)


class ModuleListViewTestCase(BaseTestCase):
    def test_list_modules(self):
        self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        self.create_module(
            product="Product2", code="CODE2", name="Module2", is_active=False
        )

        url = reverse("modules")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModuleRetrieveUpdateViewTestCase(BaseTestCase):
    def test_retrieve_module(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        url = reverse("module_detail", kwargs={"pk": module.pk})
        self.retrieve_object(url, module.pk)

    # TODO Fix this
    # def test_update_module(self):
    #     module = self.create_module(
    #         product="Product1", code="CODE2", name="Module2", is_active=True
    #     )
    #     updated_data = {
    #         "product": "Updated Product",
    #         "code": "UPDATED",
    #         "name": "Updated Module",
    #         "is_active": False,
    #     }
    #
    #     url = reverse("module_detail", kwargs={"pk": module.pk})
    #     self.update_object(url, updated_data)
    #
    #     module.refresh_from_db()
    #     self.assertEqual(module.product, "Updated Product")
    #     self.assertEqual(module.code, "UPDATED")
    #     self.assertEqual(module.name, "Updated Module")
    #     self.assertEqual(module.is_active, False)


class ModuleCompositionListViewTestCase(BaseTestCase):
    def test_list_module_compositions(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        self.create_module_composition(module=module, entity="Entity1")
        self.create_module_composition(module=module, entity="Entity2")

        url = reverse("module_composition")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModuleCompositionRetrieveViewTestCase(BaseTestCase):
    def test_retrieve_module_composition(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        module_composition = self.create_module_composition(
            module=module, entity="Entity1"
        )
        url = reverse("module_composition_detail", kwargs={"pk": module_composition.id})
        self.retrieve_object(url, module_composition.id)


class ModulePermissionListViewTestCase(BaseTestCase):
    def test_list_module_permissions(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        user_role = self.create_user_role(
            role_name="Test Role",
            description="Test Description",
            is_role_active=True,
            seeded=False,
        )
        self.create_module_permission(
            module=module,
            role=user_role,
            can_create=True,
            can_view=True,
            can_update=True,
            can_delete=False,
            is_active=True,
        )

        url = reverse("module_permission_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ModulePermissionRetrieveUpdateViewTestCase(BaseTestCase):
    def test_retrieve_module_permission(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        user_role = self.create_user_role(
            role_name="Test Role",
            description="Test Description",
            is_role_active=True,
            seeded=False,
        )
        module_permission, _ = self.create_module_permission(
            module=module,
            role=user_role,
            can_create=True,
            can_view=True,
            can_update=True,
            can_delete=False,
            is_active=True,
        )
        url = reverse("module_permission_detail", kwargs={"pk": module_permission.pk})
        self.retrieve_object(url, module_permission.pk)

    def test_update_module_permission(self):
        module = self.create_module(
            product="Product1", code="CODE1", name="Module1", is_active=True
        )
        user_role = self.create_user_role(
            role_name="Test Role 1",
            description="Test Description",
            is_role_active=True,
            seeded=False,
        )
        module_permission, _ = self.create_module_permission(
            module=module,
            role=user_role,
            can_create=True,
            can_view=True,
            can_update=True,
            can_delete=False,
            is_active=True,
        )
        updated_data = {
            "module": str(module.pk),
            "role": str(user_role.pk),
            "can_create": False,
            "can_view": True,
            "can_update": False,
            "can_delete": True,
            "is_active": False,
        }

        url = reverse("module_permission_detail", kwargs={"pk": module_permission.pk})
        self.update_object(url, updated_data)

        module_permission.refresh_from_db()
        self.assertEqual(module_permission.module, module)
        self.assertEqual(module_permission.role, user_role)
        self.assertEqual(module_permission.can_create, False)
        self.assertEqual(module_permission.can_view, True)
        self.assertEqual(module_permission.can_update, False)
        self.assertEqual(module_permission.can_delete, True)
        self.assertEqual(module_permission.is_active, False)
