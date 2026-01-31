from app.repositories.keys_repository import KeyRepository
from app.validators.key_query_validator import (
    validate_pagination,
    validate_sorting,
)
from app.utils.pagination_utils import get_offset_limit
from app.utils.logger import get_logger

logger = get_logger(__name__)


class KeyService:

    @staticmethod
    def get_keys(req):
        logger.info("get_keys called")

        req.normalize()

        page, page_size = validate_pagination(req.page, req.page_size)
        sort_field = validate_sorting(req.order_by, req.direction)

        offset, limit = get_offset_limit(page, page_size)

        keys = KeyRepository.find_all(
            offset=offset,
            limit=limit,
            order_by=sort_field,
        )

        total = KeyRepository.count_all()

        return keys, {
            "page": page,
            "page_size": page_size,
            "total": total,
            "order_by": req.order_by or "created_at",
            "direction": req.direction,
        }

    @staticmethod
    def list_ekeys(req):
        logger.info("list_ekeys called")

        req.normalize()

        page, page_size = validate_pagination(req.page, req.page_size)
        sort_field = validate_sorting(req.order_by, req.direction)

        offset, limit = get_offset_limit(page, page_size)

        keys = KeyRepository.list_keys(
            smart_lock_id=req.smart_lock_id,
            ekey_id=req.ekey_id,
            key_name=req.key_name,
            order_by=sort_field,
            offset=offset,
            limit=limit,
        )

        total = KeyRepository.count_keys(
            smart_lock_id=req.smart_lock_id,
            ekey_id=req.ekey_id,
            key_name=req.key_name,
        )

        return keys, {
            "page": page,
            "page_size": page_size,
            "total": total,
            "order_by": req.order_by or "created_at",
            "direction": req.direction,
        }

    @staticmethod
    def create_key(data):
        return KeyRepository.create_key(data)

    @staticmethod
    def delete_key(key_id):
        return KeyRepository.delete_key(key_id)
