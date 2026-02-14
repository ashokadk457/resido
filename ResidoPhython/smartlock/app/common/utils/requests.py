import time

import requests

from common.constants import EXTERNAL_API_TIMEOUT
from .logging import logger


class HelixRequests:
    def __getattribute__(self, item):
        def wrapped_request_method(*args, **kwargs):
            tags = kwargs.pop("tags", {})
            call_log = {
                "type": "CALL_LOG",
                "Meta": {**tags},
                "Request": {
                    "url": kwargs.get("url"),
                    "method": item,
                    "headers": kwargs.get("headers"),
                    "payload": kwargs.get("json"),
                },
                "Response": {},
            }
            response, exception_message = None, None
            request_method = getattr(requests, item)
            begin = time.time()
            kwargs["timeout"] = (
                kwargs.get("timeout") if kwargs.get("timeout") else EXTERNAL_API_TIMEOUT
            )
            try:
                response = request_method(*args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Exception occurred while calling external api - {str(e)}"
                )
                exception_message = str(e)
            response_time = time.time() - begin

            response_log = {
                "response_time": response_time,
                "response_time_unit": "ms",
                "response_body": None,
                "response_type": "FAILURE",
            }
            if response is None:
                response = {}
                response["errors"] = []
                error = {}
                error["code"] = "connection_error"
                error["message"] = exception_message
                response["errors"].append(error)
                response["status"] = False
                response["status_code"] = 400
                response_log["exception"] = exception_message
            else:
                status_code = response.status_code
                response_log["status_code"] = status_code
                try:
                    response_body = response.json()
                except Exception as e:
                    logger.warning(
                        f"Exception occurred while fetching response body - {str(e)}"
                    )
                    response_body = response.content.decode("utf-8")
                response_log["response_body"] = response_body
                if 200 <= status_code < 300:
                    response_log["response_type"] = "SUCCESS"

            call_log["Response"] = response_log
            logger.info(msg=None, extra=call_log)
            return response, call_log

        return wrapped_request_method


helix_request = HelixRequests()
