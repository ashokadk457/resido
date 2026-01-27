from external.lk.constants import (
    LIVEKIT_URL,
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_EMPTY_TIMEOUT,
    LIVEKIT_MAX_PARTICIPANTS,
)


class LiveKitConfiguration:
    @classmethod
    def init(cls):
        # TODO put a null safe check to see if the configuration is present in the env var

        return cls()

    def __init__(self):
        self.url = LIVEKIT_URL
        self.api_key = LIVEKIT_API_KEY
        self.api_secret = LIVEKIT_API_SECRET
        self.empty_timeout = LIVEKIT_EMPTY_TIMEOUT
        self.max_participants = LIVEKIT_MAX_PARTICIPANTS
