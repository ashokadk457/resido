ALLOWED_ORDER_FIELDS = {
    "created_at",
    "updated_at",
    "key_name",
    "ekey_id",
}

def validate_sorting(order_by: str, direction: str):
    if order_by not in ALLOWED_ORDER_FIELDS:
        order_by = "created_at"

    if direction not in ("asc", "desc"):
        direction = "desc"

    sort_field = order_by if direction == "asc" else f"-{order_by}"
    return sort_field


def validate_pagination(page, page_size):
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = int(page_size)
    except (TypeError, ValueError):
        page_size = 20

    return page, page_size
