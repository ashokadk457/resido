from django.conf import settings


class HUSConfiguration:
    @classmethod
    def init(cls):
        # TODO put a null safe check to see if the configuration is present in the env var

        return cls()

    def __init__(self):
        self.url = str(settings.SERVICES_URL)
        self.token = str(settings.SERVICES_KEY)
