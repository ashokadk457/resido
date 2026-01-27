from django.db.models import Q
from django.db.transaction import atomic

from common.utils.access_devices import (
    get_lockout_duration,
    is_within_lockout_duration,
    update_device_access,
)
from django.contrib.auth.models import update_last_login

from common.utils.datetime import DateTimeUtils
from common.utils.logging import logger
from external.kc.core import KeyCloak
from helixauth.managers.token.base import TokenManager
from helixauth.models import HelixUser
from helixauth.utils import (
    send_otp,
    verify_code,
    verify_security_answer,
    get_random_security_question,
    get_patient_or_provider_by_email,
    get_patient_or_provider_by_mobile,
)
from notifications.utils import get_staff_communication_details
from residents.models import Resident
from staff.models import HelixStaff


class HelixUserManager:
    @classmethod
    def init(cls, input_username, input_password):
        user_obj = cls.get_validated_user(input_username=input_username)
        if not user_obj:
            return

        return cls(
            user_obj=user_obj, username=user_obj.username, password=input_password
        )

    def __init__(self, **kwargs):
        self.username = kwargs.get("username")
        self.email = kwargs.get("email")
        self.phone = kwargs.get("phone")
        self.password = kwargs.get("password")
        self.serializer = kwargs.get("serializer")
        self.user_obj = kwargs.get("user_obj")
        self.user_id = str(self.user_obj.id) if self.user_obj is not None else None
        self.user_id = (
            self.user_id if self.user_id is not None else kwargs.get("user_id")
        )
        self.kc = KeyCloak.init()

        self.username = self.username if self.username else self.email
        self.username = self.username if self.username else self.phone

    @classmethod
    def get_validated_user(cls, input_username):
        try:
            return HelixUser.objects.get(
                Q(username=input_username)
                | Q(email__iexact=input_username)
                | Q(phone=input_username),
                is_active=True,
            )
        except HelixUser.DoesNotExist:
            logger.info(
                f"No user found with username or email or phone - {input_username}"
            )
            return

    def login(self):
        return self.kc.login(username=self.username, password=self.password)

    def _signup(self, user_data):
        self.password = self.password if self.password else user_data.get("password")
        auth_user_id = self.kc.signup_user(
            user_data=user_data,
            password=self.password,
        )

        return auth_user_id

    def signup(self, user_data, signup_in_kc=True):
        auth_user_id = None
        if signup_in_kc:
            auth_user_id = self._signup(user_data=user_data)

        user_data["auth_user_id"] = auth_user_id
        user_data.pop("email_verified", None)
        self.user_obj = HelixUser.objects.create(**user_data)
        if self.password:
            self.user_obj.set_password(self.password)

        return self.user_obj

    def logout(self, refresh_token):
        return self.kc.logout_user(refresh_token=refresh_token)

    def logout_tokens(self, refresh_token_tuples):
        internal_jtis = []
        for refresh_token_tuple in refresh_token_tuples:
            refresh_token = refresh_token_tuple[0]
            jti = refresh_token_tuple[1]
            if refresh_token is not None:
                self.logout(refresh_token=refresh_token)
            else:
                internal_jtis.append(jti)

        if internal_jtis:
            TokenManager.disable_all_tokens(tokens=internal_jtis)

    def _refresh(self, refresh_token):
        return self.kc.refresh_tokens(refresh_token=refresh_token)

    def refresh(self, refresh_token, reformat=True):
        fresh_tokens = self._refresh(refresh_token=refresh_token)
        if not reformat:
            return fresh_tokens
        final_data = {
            "user_id": self.user_id,  # TODO this may be empty in case of refresh
            "access": fresh_tokens.get("access_token"),
            "refresh": fresh_tokens.get("refresh_token"),
            "expires_in": DateTimeUtils.get_iso_datetime_from_now(
                offset_in_seconds=fresh_tokens.get("expires_in")
            ),
            "refresh_expires_in": fresh_tokens.get("refresh_expires_in"),
        }
        return final_data

    def _reset_password(self, password):
        return self.kc.admin.set_user_password(
            user_id=self.user_obj.auth_user_id, password=password, temporary=False
        )

    def _approve_if_pending(self):
        if self.user_obj.status == "APPROVED":
            return self.user_obj

        self.user_obj.status = "APPROVED"
        self.user_obj.is_active = True
        return self.user_obj

    @atomic
    def _change_password(self, password, approve_if_pending=False):
        self._reset_password(password=password)
        self.user_obj.set_password(password)
        if approve_if_pending:
            self.user_obj = self._approve_if_pending()
        self.user_obj.save()
        return self.user_obj

    def change_password(self, password, approve_if_pending=False):
        return self._change_password(
            password=password, approve_if_pending=approve_if_pending
        )

    def _update(self):
        return self.kc.update_user(user_obj=self.user_obj)

    def _get_associated_patient(self):
        return Resident.objects.filter(user_id=self.user_id).first()

    def _get_associated_staff(self):
        return HelixStaff.objects.filter(user_id=self.user_id).first()

    def get_associated_patient_or_provider(self):
        if self.user_obj.is_staff:
            return self._get_associated_staff(), "HelixStaff"
        return self._get_associated_patient(), "Patient"

    def get_active_approved_user(self, email):
        self.user_obj = HelixUser.objects.filter(
            email__iexact=email, is_active=True, status="APPROVED"
        ).first()
        if self.user_obj is not None:
            self.user_id = str(self.user_obj.id)
        return self.user_obj

    @classmethod
    def get_provider_via_email_or_mobile(cls, email, mobile):
        count = 0
        user = None
        mode = None
        if mobile is not None:
            user, count = get_patient_or_provider_by_mobile(mobile)
            mode = "MOBILE"
        elif email is not None:
            user, count = get_patient_or_provider_by_email(email.lower())
            mode = "EMAIL"
        if count == 0:
            raise ValueError("no_active_user")
        if count > 1:
            raise ValueError("more_than_one_account")
        return user, mode

    @classmethod
    def send_otp_to_user(cls, email, mobile):
        user, mode = cls.get_provider_via_email_or_mobile(email, mobile)
        email, phone_number, country_code = get_staff_communication_details(
            id=str(user.id)
        )
        receiving_address = phone_number if mode == "MOBILE" else email
        send_otp(
            user=user,
            type="SMS" if mode == "MOBILE" else mode,
            receiving_address=receiving_address,
            country_code=country_code,
        )
        return {"message": "OTP sent!", "type": "otp"}

    def get_validated_user_via_email_password(
        self, device_detail=None, location_detail=None
    ):
        self.user_obj = self.get_active_approved_user(email=self.email)
        if self.user_obj is None:
            raise ValueError("no_active_user")

        if is_within_lockout_duration(self.user_obj):
            raise ValueError(
                {
                    "code": "account_locked",
                    "duration": get_lockout_duration(self.user_obj),
                }
            )

        if not self.user_obj.check_password(self.password):
            update_device_access(self.user_obj, None, device_detail, location_detail)
            if self.user_obj.locked:
                raise ValueError(
                    {
                        "code": "account_locked",
                        "duration": get_lockout_duration(self.user_obj),
                    }
                )
            raise ValueError(
                {
                    "code": "incorrect_password",
                    "failed_attempt_count": self.user_obj.failed_attempt_count,
                }
            )

        return self.user_obj

    def trigger_mfa_for_staff(self):
        if self.user_obj.phone is None:
            raise ValueError("no_mobile_linked")
        return self.send_otp_to_user(email=None, mobile=self.user_obj.phone)

    def get_token_for_user_v2(
        self, associated_account=None, associated_account_class_name=None
    ):
        raw_tokens_data = self.login()
        final_data = {
            "user_id": self.user_id,
            "token": raw_tokens_data.get("access_token"),
            "refresh": raw_tokens_data.get("refresh_token"),
            "expires_in": DateTimeUtils.get_iso_datetime_from_now(
                offset_in_seconds=raw_tokens_data.get("expires_in")
            ),
            "refresh_expires_in": raw_tokens_data.get("refresh_expires_in"),
        }
        if associated_account:
            final_data["user_id"] = self.user_id
            final_data["id"] = str(associated_account.id)
            final_data["type"] = associated_account_class_name

        if associated_account and associated_account_class_name == "HelixStaff":
            final_data["access_level"] = associated_account.user.access_level
            final_data.update(
                {
                    "customer_ids": list(
                        associated_account.customers.values_list("id", flat=True)
                    )
                }
            )

        return final_data

    def update_user_last_login(self):
        if self.user_obj is not None:
            return update_last_login(sender=None, user=self.user_obj)

    def validate_and_login_with_email(self, device_detail=None, location_detail=None):
        # TODO make it work with generic username which can be either email or phone number
        self.username = self.username or self.email
        self.user_obj = self.get_validated_user_via_email_password(
            device_detail=device_detail,
            location_detail=location_detail,
        )

        (
            associated_account,
            associated_account_class_name,
        ) = self.get_associated_patient_or_provider()

        if associated_account_class_name == "Patient":
            raise ValueError("invalid_account")

        if (
            associated_account_class_name == "HelixStaff"
            and associated_account is not None
        ):
            user_roles, active_roles = associated_account.user_roles, None
            if user_roles is not None:
                active_roles = user_roles.filter(is_role_active=True)

            if active_roles is None:
                raise ValueError("user_role_inactive")

        if (
            associated_account_class_name == "HelixStaff"
            and self.user_obj.mfa_enabled in ["True", True]
        ):
            return self.trigger_mfa_for_staff()

        token_and_basics = self.get_token_for_user_v2(
            associated_account=associated_account,
            associated_account_class_name=associated_account_class_name,
        )
        update_device_access(
            user=self.user_obj,
            refresh=token_and_basics["refresh"],
            device_detail=device_detail,
            location_detail=location_detail,
        )
        self.update_user_last_login()
        return token_and_basics

    def validate_otp_and_login(
        self, mobile, email, otp, device_detail=None, location_detail={}
    ):
        staff_obj, _ = self.get_provider_via_email_or_mobile(email, mobile)
        self.user_obj = staff_obj.user
        self.user_id = str(self.user_obj.id)
        if is_within_lockout_duration(self.user_obj):
            raise ValueError(
                {
                    "code": "account_locked",
                    "duration": get_lockout_duration(self.user_obj),
                }
            )
        if not verify_code(self.user_id, 1, otp):
            update_device_access(self.user_obj, None, device_detail, location_detail)
            if self.user_obj.locked:
                raise ValueError("user_locked")
            raise ValueError("invalid_otp")
        if self.user_obj.mfa_enabled == "True" or self.user_obj.mfa_enabled is True:
            return get_random_security_question(self.user_obj)
        jwt = self.get_token_for_user_v2(
            associated_account=staff_obj, associated_account_class_name="HelixStaff"
        )
        update_device_access(
            self.user_obj, jwt["refresh"], device_detail, location_detail
        )
        update_last_login(None, self.user_obj)
        return jwt

    def validate_security_answer_and_login(
        self, question, answer, mobile, email, device_detail=None, location_detail={}
    ):
        staff_obj, _ = self.get_provider_via_email_or_mobile(email, mobile)
        self.user_obj = staff_obj.user
        self.user_id = str(self.user_obj.id)
        if is_within_lockout_duration(self.user_obj):
            raise ValueError(
                {
                    "code": "account_locked",
                    "duration": get_lockout_duration(self.user_obj),
                }
            )
        if not verify_security_answer(self.user_obj, question, answer):
            update_device_access(self.user_obj, None, device_detail, location_detail)
            if self.user_obj.locked:
                raise ValueError("user_locked")
            raise ValueError("invalid_answer")
        jwt = self.get_token_for_user_v2(
            associated_account=staff_obj, associated_account_class_name="HelixStaff"
        )
        update_device_access(
            self.user_obj, jwt["refresh"], device_detail, location_detail
        )
        update_last_login(None, self.user_obj)
        return jwt
