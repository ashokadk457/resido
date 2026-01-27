from django.db import connection
from common.utils.logging import logger
from digitalforms.models import FormReview
from digitalforms.constants import (
    FormReviewStatus,
    FORM_URL,
    SUBJECT_REVIEW_REQUESTED,
    BODY_REVIEW_REQUESTED,
    SUBJECT_FORM_REJECTED,
    BODY_FORM_REJECTED,
)
from notifications.managers.notification import NotificationsManager


class FormReviewManager:
    @staticmethod
    def trigger_review_notification(form_version):
        pending_reviewers = FormReview.objects.filter(
            form_version=form_version,
            active=True,
            status=FormReviewStatus.pending.value,
        )
        notify_to = pending_reviewers.count()
        if form_version.sequential_approval:
            pending_reviewers = pending_reviewers.order_by("sequence_number")
            notify_to = 1
        pending_reviewers = pending_reviewers.all()
        for i in range(notify_to):
            reviewer = pending_reviewers[i].reviewer
            notif_mngr = NotificationsManager(user=reviewer.staff, event_type=1)
            subj = SUBJECT_REVIEW_REQUESTED.format(form_name=form_version.form.name)
            tenant = connection.get_tenant()
            url = FORM_URL.format(domain=tenant.domain, form_version_id=form_version.id)
            body = BODY_REVIEW_REQUESTED.format(
                first_name=reviewer.staff.user.first_name,
                form_name=form_version.form.name,
                due_date=form_version.approval_due_date,
                auto_approve="set" if form_version.auto_approval else "not set",
                url=url,
            )
            notif_mngr.send_email(
                subject=subj, body=body, store_email_in_connecthub=True
            )

    @classmethod
    def on_approved_review_submission(cls, form_version):
        if form_version.sequential_approval:
            cls.start_review_process(form_version=form_version)

    @staticmethod
    def on_rejected_review_submission(form_version):
        staff = (
            form_version.created_by.helixuser_staff if form_version.created_by else None
        )
        if not staff:
            logger.error(f"Error: No created_by set for form_version {form_version.id}")
            return
        notif_mngr = NotificationsManager(user=staff, event_type=1)
        subj = SUBJECT_FORM_REJECTED.format(form_name=form_version.form.name)
        tenant = connection.get_tenant()
        url = FORM_URL.format(domain=tenant.domain, form_version_id=form_version.id)
        body = BODY_FORM_REJECTED.format(
            first_name=form_version.created_by.first_name,
            form_name=form_version.form.name,
            url=url,
        )
        notif_mngr.send_email(subject=subj, body=body, store_email_in_connecthub=True)

    @staticmethod
    def auto_approve_reviews(form_version):
        if (
            FormReview.objects.filter(
                form_version=form_version,
                active=True,
                status=FormReviewStatus.rejected.value,
            ).count()
            > 0
        ):
            logger.info(
                f"Skipping auto-approving the form_version {form_version.id} as rejected reviews exists"
            )
            return False
        all_pending_reviews = FormReview.objects.filter(
            form_version=form_version,
            active=True,
            status=FormReviewStatus.pending.value,
        )
        all_pending_reviews.update(
            status=FormReviewStatus.approved.value,
            comment="Auto-approved by the System as due date passed.",
        )
        return True
