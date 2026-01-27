from helixauth.models import HelixUser, UserRole
from helixauth.managers.verificationcode import VerificationCodeManager
from staff.models import HelixStaff
from common.utils.access_devices import update_device_access


class AdminManager:
    def create_tenant_admin(self, email):
        user, _ = HelixUser.objects.get_or_create(
            email__iexact=email,
            defaults={"email": email, "is_superuser": True, "is_active": False},
        )
        # TODO - Assign the right role
        role = UserRole.objects.filter(role_name="Site Administrator").first()
        provider, _ = HelixStaff.objects.get_or_create(user=user)
        provider.user_roles.set([role])
        return provider

    def validate_otp_and_activate_user(self, email, otp, attrs=None):
        user = HelixStaff.objects.get(user__email__iexact=email)
        if VerificationCodeManager.is_code_valid(
            user_ids=[user.user.id], user_type=1, code=otp
        ):
            user.user.is_active = True
            user.user.save()
            return user
        else:
            update_device_access(
                user,
                None,
                attrs.get("device_detail", {}),
                attrs.get("location_detail", {}),
            )
            return False
