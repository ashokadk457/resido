# from django.core.files.uploadedfile import SimpleUploadedFile
# from django.urls import reverse
# from rest_framework import status
#
# from assets.models import Asset
# from common.tests import BaseTenantTestCase
# from helixauth.models import HelixUser, UserRole
# from staff.models import HelixStaff


# class TestListCreateAsset(BaseTenantTestCase):
#     def setUp(self):
#         with self.settings(DEFAULT_FILE_STORAGE="inmemorystorage.InMemoryStorage"):
#             super().setUp()
#             file = SimpleUploadedFile(name="file.txt", content=b"test")
#             self.url = reverse("asset_list_create")
#
#             user = HelixUser(email="test@mailinator.com", is_active=True)
#             self.client.force_login(user)
#             password = "Test123!"
#             user.set_password(password)
#             user.save()
#             self.user_role, _ = UserRole.objects.get_or_create(
#                 role_name="Test",
#                 defaults={
#                     "seeded": False,
#                 },
#             )
#             HelixStaff.objects.create(
#                 user=user, user_role=self.user_role
#             )  # need to provide user_role_id
#             headers = {
#                 "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
#             }
#             login_url = reverse('login')
#             self.token = self.client.post(
#                 login_url,
#                 data={"email": user.email, "password": password},
#                 content_type="application/json",
#                 **headers,
#             ).data["data"]["token"]
#
#             Asset.objects.create(file=file, created_by=user, filename="file.txt")
#
#     def test_create_asset(self):
#         with self.settings(DEFAULT_FILE_STORAGE="inmemorystorage.InMemoryStorage"):
#             file = SimpleUploadedFile(name="file.txt", content=b"test")
#             request_payload = {"type": "doc", "file": file, "filename": "file.txt"}
#             response = self.client.post(
#                 path=self.url,
#                 data=request_payload,
#                 HTTP_AUTHORIZATION="Bearer " + self.token,
#             )
#             self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
#     def test_list_asset(self):
#         with self.settings(DEFAULT_FILE_STORAGE="inmemorystorage.InMemoryStorage"):
#             response = self.client.get(
#                 path=self.url, HTTP_AUTHORIZATION="Bearer " + self.token
#             )
#             self.assertEqual(response.status_code, status.HTTP_200_OK)


# class TestRetrieveAsset(BaseTenantTestCase):
#     def setUp(self):
#         with self.settings(DEFAULT_FILE_STORAGE="inmemorystorage.InMemoryStorage"):
#             super().setUp()
#             self.file = SimpleUploadedFile(name="file.txt", content=b"test")
#
#             user = HelixUser(email="test@mailinator.com", is_active=True)
#             self.user_role, _ = UserRole.objects.get_or_create(
#                 role_name="Test",
#                 defaults={
#                     "seeded": False,
#                 },
#             )
#             self.client.force_login(user)
#             password = "Test123!"
#             user.set_password(password)
#             user.save()
#             HelixStaff.objects.create(user=user, user_role=self.user_role)
#             login_url = reverse('login')
#             headers = {
#                 "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
#             }
#             self.token = self.client.post(
#                 login_url,
#                 data={"email": user.email, "password": password},
#                 content_type="application/json",
#                 **headers,
#             ).data["data"]["token"]
#
#             asset = Asset.objects.create(
#                 file=self.file, created_by=user, filename="file.txt"
#             )
#             self.url = reverse("asset_detail", kwargs={"pk": asset.id})
#
#     def test_retrieve_asset(self):
#         with self.settings(DEFAULT_FILE_STORAGE="inmemorystorage.InMemoryStorage"):
#             response = self.client.get(
#                 path=self.url, HTTP_AUTHORIZATION="Bearer " + self.token
#             )
#             self.assertEqual(response.status_code, status.HTTP_200_OK)
