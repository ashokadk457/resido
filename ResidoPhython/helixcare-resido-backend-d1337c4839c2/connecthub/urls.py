from django.urls import re_path

from .apiviews import (
    BulkMarkEmailAsReadAPIView,
    CreateListEmailAPIView,
    CreateListSMSAPIView,
    MarkEmailAsReadAPIView,
    SMSInboxView,
    UpdateDraftToSentAPIView,
    EmailTemplateCreateListAPIView,
    EmailTemplateRetrieveUpdateDestroyAPIView,
)

urlpatterns = [
    re_path(
        r"^api/v1/connecthub/emails$",
        CreateListEmailAPIView.as_view(),
        name="create-list-emails",
    ),
    re_path(
        r"api/v1/connecthub/emails/bulk-read-unread$",
        BulkMarkEmailAsReadAPIView.as_view(),
        name="bulk-read-unread-emails",
    ),
    re_path(
        r"^api/v1/connecthub/emails/(?P<pk>[0-9a-zA-Z\-]+)$",
        UpdateDraftToSentAPIView.as_view(),
        name="draft-to-emails",
    ),
    re_path(
        r"api/v1/connecthub/emails/(?P<email_id>[0-9a-zA-Z\-]+)/mark-as-read$",
        MarkEmailAsReadAPIView.as_view(),
        name="mark-email-as-read",
    ),
    re_path(
        r"^api/v1/connecthub/sms$",
        CreateListSMSAPIView.as_view(),
        name="create-list-sms",
    ),
    re_path(
        r"^api/v1/connecthub/sms/inbox$",
        SMSInboxView.as_view(),
        name="create-list-sms",
    ),
    re_path(
        r"^api/v1/connecthub/email-templates$",
        EmailTemplateCreateListAPIView.as_view(),
        name="email-templates",
    ),
    re_path(
        r"^api/v1/connecthub/email-templates/(?P<pk>[0-9a-zA-Z\-]+)$",
        EmailTemplateRetrieveUpdateDestroyAPIView.as_view(),
        name="email-templates",
    ),
]
