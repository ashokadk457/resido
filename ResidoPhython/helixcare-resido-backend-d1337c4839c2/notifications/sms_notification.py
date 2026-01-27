import json

from common.utils.logging import logger
from notifications.apiviews import sendSMS
from notifications.helix_notification import HelixNotification
from notifications.utils import Utils


class SMSNotification(HelixNotification):
    @staticmethod
    def number_validation_required(notification_settings):
        """

        TODO: Temporary method to check if number validation is required.
        TODO: Will be removed once number validation api is purchased.

        @param notification_settings:
        @return: Bool
        """
        validation_config = notification_settings.message
        if not validation_config:
            return True
        try:
            validation_config = json.loads(validation_config)
        except Exception as e:
            logger.info(f"Exception occurred while parsing validation config: {str(e)}")
            return True

        return validation_config.get("validate_number", True)

    def send(self, entry):
        util = Utils()
        notif_settings = entry.notification_setting

        is_number_validation_required = self.number_validation_required(
            notification_settings=notif_settings
        )
        number_is_valid = True
        if is_number_validation_required:
            logger.info("Number validation required")
            number_is_valid = util.validate_number(entry.receiving_address)

        if number_is_valid:
            logger.info(f"Sending SMS to {entry.receiving_address}")
            ret = sendSMS(
                to=entry.receiving_address,
                message=entry.payload.get("message"),
                sender_id=None,
                rec_id=None,
            )
            logger.info(f"sendSMS response is: {ret}")
            if ret["status_code"] in (200, 201, 202):
                logger.info("SMS is sent successfully")
                util.update_queue(entry, 1, "Success!")
            else:
                logger.info(f"Error occurred while sending SMS: {ret}")
                util.update_queue(entry, 2, ret.get("message"))
        else:
            util.update_queue(entry, 2, "Invalid Number")
