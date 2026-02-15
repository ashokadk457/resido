import logging


class Utils:
    
    @staticmethod
    def get_logger(name: str):
        logger = logging.getLogger(name)

        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

        return logger
    
    @staticmethod
    def pagination_offset_limit(page: int, page_size: int):
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)  # hard cap

        offset = (page - 1) * page_size
        limit = page_size

        return offset, limit
    
    