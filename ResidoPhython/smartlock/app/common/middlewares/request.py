import json
from log_request_id import local
from django.urls import resolve
from common.models import Domain
from django_tenants.utils import tenant_context
from common.utils.logging import logger
from common.thread_locals import set_current_user, get_current_user
from audit.kafka_audit import KafkaAudit

kafka_audit = KafkaAudit()


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    @staticmethod
    def _format_request_body(request, request_headers, request_body):
        if not request_body or not request_headers:
            return request_body

        request_body = request_body.decode("utf-8")
        if request_headers.get("Content-Type") == "application/json":
            return json.loads(request_body)
        if (
            request_headers.get("Content-Type") == "application/x-www-form-urlencoded"
        ) or (request_headers.get("Content-Type", "").startswith("multipart")):
            return dict(request.POST)
        return request_body

    def get_base_request_log(self, request):
        base_log = {}
        try:
            base_log = {
                "method": request.method,
                "path": request.path,
                "request_headers": dict(request.headers),  # TODO can filter out headers
            }
            # TODO can mask any PII data in request params/body if required
            if base_log["method"] == "GET":
                base_log["request_params"] = dict(request.GET)
            else:
                base_log["request_body"] = self._format_request_body(
                    request=request,
                    request_headers=base_log["request_headers"],
                    request_body=request.body,
                )
        except Exception as e:
            logger.warning(f"Exception occurred while creating request log: {str(e)}")
        return base_log

    @staticmethod
    def get_response_log(response):
        response_log = {}
        try:
            status_code = None
            if hasattr(response, "status_code"):
                status_code = response.status_code
            if (
                status_code
                and status_code >= 500
                and hasattr(response, "reason_phrase")
            ):
                response_log["response_body"] = response.reason_phrase
            elif status_code and status_code < 500 and hasattr(response, "data"):
                response_log["response_body"] = response.data
            response_log["status_code"] = status_code
        except Exception as e:
            logger.warning(f"Exception occurred while creating response log- {str(e)}")

        # remove the user from the thread to be safe
        set_current_user(None)

        return response_log

    @staticmethod
    def check_if_request_be_logged(request):
        try:
            path = request.path
            return path.startswith("/api")
        except Exception as e:
            logger.warning(
                f"Exception occurred while checking request logging status- {str(e)}"
            )
        return False

    @staticmethod
    def save_ip_address_from_request(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        setattr(local, "ip_address", ip)

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        log_request_response, base_log = (
            self.check_if_request_be_logged(request=request),
            {},
        )
        setattr(local, "user_agent", request.headers.get("User-Agent", None))
        self.save_ip_address_from_request(request)

        if log_request_response:
            base_log = self.get_base_request_log(request=request)
            request_log = {"type": "API_REQUEST", **base_log}
            logger.info(msg=None, extra=request_log)

        response = self.get_response(request)

        if log_request_response:
            response_log = self.get_response_log(response=response)
            response_log = {"type": "API_RESPONSE", **base_log, **response_log}
            logger.info(msg=None, extra=response_log)
            # if request.method in ["GET"]:
            #     self.log_audit(request, response_log)

        return response

    def log_audit(self, request, response_log):
        hostname = request.get_host().split(".")[0]
        domain = Domain.objects.filter(domain__contains=hostname).first()
        tenant = domain.tenant
        if tenant.schema_name == "public":
            return
        resolved_value = resolve(request.path)
        if resolved_value:
            try:
                url_name = resolved_value.url_name
                if self._is_excluded(url_name):
                    return
                with tenant_context(tenant):
                    kafka_audit.publish(
                        {
                            **response_log,
                            "url": url_name,
                            "schema": tenant.schema_name,
                            "type": "READ",
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to log audit: {str(e)}")
        else:
            logger.warning(f"Unresolved request to {request.path}")

    @staticmethod
    def _is_excluded(url_name):
        excluded = ["list-audit-events", "audit-events-detail"]
        return url_name in excluded

    @staticmethod
    def get_user():
        current_user = get_current_user()
        return current_user
