import asyncio

from livekit.api import LiveKitAPI, CreateRoomRequest
from external.lk.configuration import LiveKitConfiguration


class LiveKit:
    @classmethod
    def init(cls, config: LiveKitConfiguration):
        return cls(config=config)

    def __init__(self, config: LiveKitConfiguration):
        self.config = config
        self._loop = asyncio.new_event_loop()
        self.livekit_client = self.init_livekit_client()

    async def _init_livekit_client(self):
        return LiveKitAPI(
            url=self.config.url,
            api_key=self.config.api_key,
            api_secret=self.config.api_secret,
        )

    def init_livekit_client(self):
        future_client = asyncio.ensure_future(
            self._init_livekit_client(), loop=self._loop
        )
        return self._loop.run_until_complete(future_client)

    async def _create_room(self, room_name):
        return await self.livekit_client.room.create_room(
            CreateRoomRequest(
                name=room_name,
                empty_timeout=self.config.empty_timeout,
                max_participants=self.config.max_participants,
            )
        )

    def create_room(self, room_name):
        future_room = asyncio.ensure_future(
            self._create_room(room_name=room_name), loop=self._loop
        )
        return self._loop.run_until_complete(future_room)
