class HelixNotificationSender:
    def sender(self, notificationInst, entry):
        notificationInst.send(entry)
