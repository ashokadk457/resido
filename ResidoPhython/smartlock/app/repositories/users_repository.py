from django.db.models import Q, F
from app.models.user_model import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UsersRepository:
    """
    Repository layer for Users table
    """

    @staticmethod
    def _base_queryset(
        first_name=None,
        last_name=None,
        email=None,
        dial_code=None,
        phone_number=None,
        ttlock_username=None,
        is_phone_verified=None,
        is_email_verified=None,
        is_active=None,
        user_status=None,
        user_type=None,
    ):
        qs = User.objects.all()

        if first_name:
            qs = qs.filter(Q(first_name__icontains=first_name))

        if last_name:
            qs = qs.filter(Q(last_name__icontains=last_name))

        if email:
            qs = qs.filter(Q(email__icontains=email))

        if dial_code:
            qs = qs.filter(dial_code=dial_code)

        if phone_number:
            qs = qs.filter(phone_number=phone_number)

        if ttlock_username:
            qs = qs.filter(Q(ttlock_username__icontains=ttlock_username))

        if is_phone_verified is not None:
            qs = qs.filter(is_phone_verified=is_phone_verified)

        if is_email_verified is not None:
            qs = qs.filter(is_email_verified=is_email_verified)

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        if user_status is not None:
            qs = qs.filter(user_status=user_status)

        if user_type is not None:
            qs = qs.filter(user_type=user_type)

        return qs

    @staticmethod
    def find_all(offset, limit, order_by):
        logger.debug("find_all offset=%s limit=%s order_by=%s", offset, limit, order_by)
        return User.objects.order_by(order_by)[offset: offset + limit]

    @staticmethod
    def count_all():
        logger.debug("count_all called")
        return User.objects.count()

    @staticmethod
    def list_users(
        first_name=None,
        last_name=None,
        email=None,
        dial_code=None,
        phone_number=None,
        ttlock_username=None,
        is_phone_verified=None,
        is_email_verified=None,
        is_active=None,
        user_status=None,
        user_type=None,
        order_by="created_at",
        offset=0,
        limit=20,
    ):
        logger.debug(
            "list_users first_name=%s last_name=%s email=%s phone_number=%s is_active=%s",
            first_name, last_name, email, phone_number, is_active
        )

        qs = UsersRepository._base_queryset(
            first_name=first_name,
            last_name=last_name,
            email=email,
            dial_code=dial_code,
            phone_number=phone_number,
            ttlock_username=ttlock_username,
            is_phone_verified=is_phone_verified,
            is_email_verified=is_email_verified,
            is_active=is_active,
            user_status=user_status,
            user_type=user_type,
        )

        return qs.order_by(order_by)[offset: offset + limit]

    @staticmethod
    def count_users(
        first_name=None,
        last_name=None,
        email=None,
        dial_code=None,
        phone_number=None,
        ttlock_username=None,
        is_phone_verified=None,
        is_email_verified=None,
        is_active=None,
        user_status=None,
        user_type=None,
    ):
        logger.debug("count_users called")

        qs = UsersRepository._base_queryset(
            first_name=first_name,
            last_name=last_name,
            email=email,
            dial_code=dial_code,
            phone_number=phone_number,
            ttlock_username=ttlock_username,
            is_phone_verified=is_phone_verified,
            is_email_verified=is_email_verified,
            is_active=is_active,
            user_status=user_status,
            user_type=user_type,
        )

        return qs.count()

    @staticmethod
    def get_by_id(user_id):
        logger.debug("get_by_id user_id=%s", user_id)
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @staticmethod
    def find_by_email(email):
        logger.debug("find_by_email email=%s", email)
        try:
            return User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            return None

    @staticmethod
    def find_by_phone(phone_number):
        logger.debug("find_by_phone phone_number=%s", phone_number)
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return None

    @staticmethod
    def find_by_ttlock_username(ttlock_username):
        logger.debug("find_by_ttlock_username ttlock_username=%s", ttlock_username)
        try:
            return User.objects.get(ttlock_username=ttlock_username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def create_user(data):
        logger.info("create_user called")
        return User.objects.create(**data)

    @staticmethod
    def update_user(user_id, data):
        logger.info("update_user called user_id=%s", user_id)
        updated = User.objects.filter(id=user_id).update(**data)
        return updated > 0

    @staticmethod
    def increment_failed_attempts(user_id, increment=1):
        logger.info("increment_failed_attempts user_id=%s increment=%s", user_id, increment)
        updated = User.objects.filter(id=user_id).update(failed_login_attempts=F('failed_login_attempts') + increment)
        return updated > 0

    @staticmethod
    def reset_failed_attempts(user_id):
        logger.info("reset_failed_attempts user_id=%s", user_id)
        updated = User.objects.filter(id=user_id).update(failed_login_attempts=0)
        return updated > 0

    @staticmethod
    def set_last_login(user_id, timestamp):
        logger.info("set_last_login user_id=%s timestamp=%s", user_id, timestamp)
        updated = User.objects.filter(id=user_id).update(last_login=timestamp)
        return updated > 0

    @staticmethod
    def update_password(user_id, password_hash, password_salt=None):
        logger.info("update_password user_id=%s", user_id)
        data = {"password_hash": password_hash}
        if password_salt is not None:
            data["password_salt"] = password_salt
        updated = User.objects.filter(id=user_id).update(**data)
        return updated > 0

    @staticmethod
    def delete_user(user_id):
        logger.warning("delete_user called user_id=%s", user_id)
        deleted, _ = User.objects.filter(id=user_id).delete()
        return deleted > 0
