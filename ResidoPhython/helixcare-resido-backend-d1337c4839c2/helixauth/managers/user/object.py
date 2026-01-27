from django.contrib.auth.models import UserManager
from django.forms import model_to_dict
from django.db.models import Q

from common.managers.model.generic import GenericModelManager
from external.kc.core import KeyCloak


class HelixUserObjectManager(UserManager, GenericModelManager):
    @staticmethod
    def _create_user_in_keycloak(user, password):
        user_data = model_to_dict(user)
        kc = KeyCloak.init()
        if not kc:
            raise Exception("KeyCloak not configured")

        auth_user_id = kc.signup_user(
            user_data=user_data,
            password=password,
        )
        user.auth_user_id = auth_user_id
        user.save()
        return user

    def _create_user(self, username, email, password, **extra_fields):
        user = super(HelixUserObjectManager, self)._create_user(
            username, email, password, **extra_fields
        )
        return self._create_user_in_keycloak(user=user, password=password)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("access_level", "admin")
        extra_fields.setdefault("status", "APPROVED")
        return self._create_user(username, email, password, **extra_fields)

    @classmethod
    def is_user_with_email_phone_number_exists(cls, email, phone_number):
        from helixauth.models import HelixUser

        if not email and not phone_number:
            return False

        queries = Q()
        if email:
            queries = Q(email__iexact=email)
        if phone_number:
            queries = queries | Q(phone=phone_number)
        return HelixUser.objects.filter(queries).exists()
