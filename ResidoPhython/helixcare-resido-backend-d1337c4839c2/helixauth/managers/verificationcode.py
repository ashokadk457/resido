from datetime import datetime
from typing import List

from common.constants import UTC_TIMEZONE, OTP_EXPIRY_IN_SECONDS
from common.managers.model.base import BaseModelManager
from common.utils.logging import logger
from helixauth.models import VerificationCode
from helixauth.utils import send_otp, generate_code
from residents.managers.patient import ResidentManager
from staff.managers.helixstaff import HelixStaffManager


class VerificationCodeManager(BaseModelManager):
    model = VerificationCode
    EMPTY_VERIFICATION_DATA = {"user_ids": [None], "user_type": None, "code": None}

    def __init__(self, user_ids=None, user_type=None, code=None, **kwargs):
        super(VerificationCodeManager, self).__init__(**kwargs)
        self.user_ids = user_ids
        self.user_type = user_type
        self.code = code
        self.verification_code_obj = None
        self.is_verified = False

    def is_valid_code_v2(self):
        if not self.user_ids and not self.user_type and not self.code:
            return False, None

        self.verification_code_obj = self.get_verification_code_obj()
        if not self.verification_code_obj:
            return False, None

        if self.has_verification_code_expired():
            logger.info("Verification code expired")
            self.delete()
            return False, None

        # Not deleting the code here since the code has to be manually deleted
        self.is_verified = True
        return True, self.verification_code_obj.channel

    def delete(self):
        return self._delete(verification_code_obj=self.verification_code_obj)

    @classmethod
    def _delete(cls, verification_code_obj):
        if not verification_code_obj:
            return
        verification_code_obj.delete()

    @classmethod
    def is_code_valid(cls, user_ids: List, user_type: int, code: str) -> bool:
        if not user_ids or not user_type or not code:
            return False

        verification_code_obj = cls._get_verification_code_obj(
            user_ids=user_ids, user_type=user_type, code=code
        )
        if not verification_code_obj:
            return False

        if cls._has_verification_code_expired(
            verification_code_obj=verification_code_obj
        ):
            logger.info("Verification code expired")
            cls._delete(verification_code_obj=verification_code_obj)
            return False

        cls._delete(verification_code_obj=verification_code_obj)
        return True

    @staticmethod
    def validate_channel_for_user(user, channel):
        if channel == "EMAIL" and user.email is None:
            return False, "channel_not_allowed"
        if channel == "SMS" and user.phone_number is None:
            return False, "channel_not_allowed"
        return True, None

    @classmethod
    def resend_code(cls, user_id, user_type, channel):
        user = None
        if user_type == 1:
            user = HelixStaffManager().get_provider(staff_id=user_id)
        elif user_type == 2:
            user = ResidentManager().get_resident(patient_id=user_id)
        else:
            return False, "invalid_user_type"

        if not user:
            return False, "user_not_found"

        valid, error_code = cls.validate_channel_for_user(user, channel)
        if not valid:
            return False, error_code

        try:
            send_otp(user, channel)
        except Exception:
            return False, "something_went_wrong"

        return True, None

    @classmethod
    def create_verification_code(
        cls, user_id, user_type, mode="update_or_create", channel=None
    ):
        code = generate_code()
        if mode == "update_or_create":
            return VerificationCode.objects.update_or_create(
                user_id=user_id,
                user_type=user_type,
                channel=channel,
                defaults={"code": code},
            )

    def get_verification_code_obj(self):
        self.verification_code_obj = self._get_verification_code_obj(
            user_ids=self.user_ids, user_type=self.user_type, code=self.code
        )
        return self.verification_code_obj

    @classmethod
    def _get_verification_code_obj(cls, user_ids=None, user_type=None, code=None):
        return cls.model.objects.filter(
            user_id__in=user_ids, user_type=user_type, code=code
        ).first()

    def has_verification_code_expired(self):
        return self.__class__._has_verification_code_expired(
            verification_code_obj=self.verification_code_obj
        )

    @classmethod
    def _has_verification_code_expired(cls, verification_code_obj):
        current_time = datetime.now(tz=UTC_TIMEZONE)
        updated_on = verification_code_obj.updated_on

        delta = current_time - updated_on

        if delta.days > 0:
            # code has expired
            return True

        return delta.seconds >= OTP_EXPIRY_IN_SECONDS
