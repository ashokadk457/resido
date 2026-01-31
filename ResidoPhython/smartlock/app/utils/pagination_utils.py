def get_offset_limit(page: int, page_size: int):
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)  # hard cap

    offset = (page - 1) * page_size
    limit = page_size

    return offset, limit
