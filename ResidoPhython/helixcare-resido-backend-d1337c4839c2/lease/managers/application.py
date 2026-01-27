import time
from django.db import connection
from django.template.loader import render_to_string
from rest_framework.serializers import ValidationError
from common.errors import ERROR_DETAILS
from notifications.managers.notification import NotificationsManager
from helixauth.token.resident.access import ResidentAccessToken
from lease.constants import (
    LEASE_APPLICATION_EMAIL_SUBJECT,
    LEASE_APPLICATION_FORM_URL,
    LEASE_APPLICATION_FORM_LINK_EXPIRY,
    LeaseApplicationStatus,
)


class ApplicationManager:
    def __init__(self, instance):
        self.obj = instance

    def _get_token(self):
        reset_password_token_expiry = (
            int(time.time()) + LEASE_APPLICATION_FORM_LINK_EXPIRY
        )
        common_token_identity = {
            "tenant": connection.tenant,
            "expiry": reset_password_token_expiry,
            "sub_token_type": "rental_request_form",
        }
        rental_request_form_token = str(
            ResidentAccessToken.for_tenant_resident(
                resident=self.obj.resident, **common_token_identity
            )
        )
        return rental_request_form_token

    def send_email(self):
        if self.obj.status != LeaseApplicationStatus.SENT.value:
            raise ValidationError(
                code="action_not_allowed",
                detail=ERROR_DETAILS["action_not_allowed"],
            )
        mngr = NotificationsManager(user=self.obj.resident)
        domain = connection.tenant.domain
        url = LEASE_APPLICATION_FORM_URL.format(
            domain=domain, request_id=str(self.obj.id), token=str(self._get_token())
        )

        # Get property/customer name
        property_name = connection.tenant.name if connection.tenant else "Resido"

        # Prepare template context
        context = {
            "applicant_name": self.obj.resident.user.first_name,
            "property_name": property_name,
            "application_url": url,
            "logo_url": None,  # Add logo URL if available
            "expiry_note": "This link will expire after some time. If you have any questions, please reach out to us.",
        }

        # Render HTML template
        body = render_to_string("email/lease_application.html", context)
        subject = LEASE_APPLICATION_EMAIL_SUBJECT

        mngr.send_email(subject=subject, body=body)
