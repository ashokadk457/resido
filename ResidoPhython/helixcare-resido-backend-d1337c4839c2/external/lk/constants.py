import os

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://falcon-313g44ar.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "APIbymJWvDDydaE")
LIVEKIT_API_SECRET = os.getenv(
    "LIVEKIT_API_SECRET", "jAx5YvRrFgpjzVYYzYNvuFeSXKmfmfmRi2Nuje9srsNC"
)
LIVEKIT_EMPTY_TIMEOUT = int(os.getenv("LIVEKIT_EMPTY_TIMEOUT", 45))
LIVEKIT_MAX_PARTICIPANTS = int(os.getenv("LIVEKIT_MAX_PARTICIPANTS", 20))
