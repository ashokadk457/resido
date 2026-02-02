from django.db.models import Q
from app.models.key_model import Key
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KeyRepository:
    """
    Repository layer for Key model interactions.:
    """

    # Base queryset
    @staticmethod
    def _base_queryset(
        smart_lock_id=None,
        ekey_id=None,
        key_name=None,
    ):
        qs = Key.objects.all()

        if smart_lock_id:
            qs = qs.filter(smart_lock_id=smart_lock_id)

        if ekey_id:
            qs = qs.filter(ekey_id=ekey_id)

        if key_name:
            qs = qs.filter(
                Q(key_name__icontains=key_name)
            )

        return qs

    # GET KEYS
    @staticmethod
    def find_all(offset, limit, order_by):
        logger.debug(
            "find_all offset=%s limit=%s order_by=%s",
            offset, limit, order_by
        )

        return (
            Key.objects
            .order_by(order_by)
            [offset: offset + limit]
        )

    @staticmethod
    def count_all():
        logger.debug("count_all called")
        return Key.objects.count()

    # LIST KEYS 
    @staticmethod
    def list_keys(
        smart_lock_id=None,
        ekey_id=None,
        key_name=None,
        order_by="created_at",
        offset=0,
        limit=20,
    ):
        logger.debug(
            "list_keys smart_lock_id=%s ekey_id=%s key_name=%s",
            smart_lock_id, ekey_id, key_name
        )

        qs = KeyRepository._base_queryset(
            smart_lock_id=smart_lock_id,
            ekey_id=ekey_id,
            key_name=key_name,
        )

        return qs.order_by(order_by)[offset: offset + limit]

    @staticmethod
    def count_keys(
        smart_lock_id=None,
        ekey_id=None,
        key_name=None,
    ):
        logger.debug(
            "count_keys smart_lock_id=%s ekey_id=%s key_name=%s",
            smart_lock_id, ekey_id, key_name
        )

        qs = KeyRepository._base_queryset(
            smart_lock_id=smart_lock_id,
            ekey_id=ekey_id,
            key_name=key_name,
        )

        return qs.count()

    # WRITE OPERATIONS
    @staticmethod
    def create_key(data):
        logger.info("create_key called")
        return Key.objects.create(**data)

    @staticmethod
    def delete_key(key_id):
        logger.warning("delete_key called key_id=%s", key_id)
        deleted, _ = Key.objects.filter(id=key_id).delete()
        return deleted > 0
