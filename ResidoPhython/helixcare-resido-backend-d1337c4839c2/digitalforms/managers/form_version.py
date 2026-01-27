from datetime import datetime
from common.utils.logging import logger
from digitalforms.models import FormVersion
from digitalforms.constants import FormStatus
from digitalforms.managers.form_review import FormReviewManager


class FormVersionManager:
    @staticmethod
    def get_due_dated_pending_form_versions_having_auto_approval(due_date):
        return FormVersion.objects.filter(
            approval_due_date__lt=due_date,
            auto_approval=True,
            status=FormStatus.in_review.value,
        )

    @classmethod
    def check_auto_approval_form_versions(cls):
        today_date = datetime.now().date()
        pending_versions = cls.get_due_dated_pending_form_versions_having_auto_approval(
            due_date=today_date
        )
        for vrsn in pending_versions:
            if FormReviewManager.auto_approve_reviews(form_version=vrsn):
                vrsn.status = FormStatus.approved.value
                vrsn.save()
                logger.info(f"Auto-approved form_version {vrsn.id} successfully.")
