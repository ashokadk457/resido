from common.utils.logging import logger
from notifications.apiviews import sendEmail
from notifications.helix_notification import HelixNotification


class EmailNotification(HelixNotification):
    def send(self, entry):
        SENT = 1
        FAILED = 2

        # Use receiving_address which contains the redirected email (if TEST_EMAIL_ID is set)
        email = entry.receiving_address

        # Get ID for tracking purposes
        id = None
        if entry.user:
            id = str(entry.user.id)
        elif entry.provider:
            id = str(entry.provider.id)

        try:
            logger.info(f"Sending email to {email}")
            ret = sendEmail(
                entry.payload.get("subject"),
                entry.payload.get("message"),
                [email],
                None,
                id,
                html_message=entry.payload.get("html_message"),
            )
        except Exception as err:
            logger.error(err)
            entry.status = FAILED
            entry.error_code = repr(err)
            entry.save()
            return

        if ret.get("status_code") == 200:
            logger.info(f"Email sent to {email}")
            entry.status = SENT
        else:
            entry.status = FAILED
            entry.error_code = repr(ret["message"])[:100]
        entry.save()
