from functools import lru_cache

from common.managers.model.base import BaseModelManager
from lookup.models import Lookup
from scheduling.models import EventTitleAvailability


class TitleAvailabilityManager(BaseModelManager):
    model = EventTitleAvailability

    @classmethod
    @lru_cache(maxsize=512)
    def filter_by_available_for_appointment(cls, available_for_appointment):
        return EventTitleAvailability.objects.filter_from_cache(
            available_for_appointment=available_for_appointment
        )

    @classmethod
    @lru_cache(maxsize=512)
    def filter_by_title(cls, title):
        return EventTitleAvailability.objects.filter_from_cache(event_title=title)

    @classmethod
    def populate_default_availabilities(cls):
        all_event_titles = [
            c.get("code")
            for c in Lookup.objects.filter(name="EVENT_TITLE").values("code")
        ]

        objs = []
        for event_title in all_event_titles:
            row = cls.model.objects.filter(
                event_title=event_title,
                available_for_appointment=event_title == "AVAILABLE",
            )
            if row:
                continue
            obj = cls.model(
                event_title=event_title,
                available_for_appointment=event_title == "AVAILABLE",
            )

            objs.append(obj)

        cls.model.objects.bulk_create(objs)
