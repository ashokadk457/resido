import logging
import uuid
from log_request_id import local

from json_log_formatter import JSONFormatter

from common.constants import HB_LOGGER

logger = logging.getLogger(HB_LOGGER)


class StandardJSONLogFormatter(JSONFormatter):
    def json_record(self, message, extra, record):
        request = extra.pop("request", None)
        if request:
            # Add any other parameter
            extra["IP_ADDRESS"] = request.META.get(
                "HTTP_X_FORWARDED_FOR"
            )  # or other ways to get ip
        additional_info = {
            "name": record.name,
            "level": record.levelname,
            "file": record.filename,
            "exc_info": record.exc_info,
            "thread": record.thread,
        }
        extra = {**extra, **additional_info}
        return super(StandardJSONLogFormatter, self).json_record(message, extra, record)


def set_request_id(request_id):
    setattr(local, "request_id", request_id)


def get_request_id():
    request_id = getattr(local, "request_id", uuid.uuid4())
    return request_id


def assign_request_id_to_local_thread(func):
    """

        Decorator to assign a request_id to the local thread.
        Helpful in request_id logging, filtering and tracing requests.

    Args:
        func:

    Returns:

    """

    def wrapped_function(*args, **kwargs):
        try:
            request_id = kwargs.get("request_id", uuid.uuid4())
            set_request_id(request_id=request_id)
        except Exception as e:
            logger.info(f"Exception occurred while assigning request_id - {str(e)}")
        return func(*args, **kwargs)

    return wrapped_function
