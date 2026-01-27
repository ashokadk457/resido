from notifications.helix_notification import HelixNotification
from notifications.utils import Utils


class VoiceNotification(HelixNotification):
    def send(self, entry):
        util = Utils()
        if util.validate_number(entry.payload["to"], "123"):
            try:
                URL = "https://shanmugam.cambodiapbx.com/robocall/reminder.php?id="
                URL += entry.id
                URL += "&msisdn="
                URL += entry.payload["to"]
                URL += "&message='"
                URL += entry.payload["message"]
                URL += "'&mode=1&token='123456'"
                util.update_queue(entry, 1)
            except Exception:
                util.update_queue(entry, 2, "Error while calling url")
        else:
            util.update_queue(entry, 2, "Invalid Number")
