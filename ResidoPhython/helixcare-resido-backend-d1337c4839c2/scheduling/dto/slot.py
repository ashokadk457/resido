from dataclasses import dataclass
from datetime import datetime


@dataclass
class SlotDTO:
    id: any
    event_id: any
    event_name: str
    event_title: str
    practice_location_id: any
    practice_location_name: str
    event_start_time: str
    event_end_time: str
    event_update_id: any
    event_update_for_date: str
    visit_type: str
    visit_type_duration: any
    slot_start_time: datetime
    slot_end_time: datetime

    def data(self):
        return self.__dict__

    @classmethod
    def init(
        cls,
        event_block: dict,
        slot_start_time: datetime,
        slot_end_time: datetime,
        visit_type: str,
        visit_type_duration: any,
    ):
        return SlotDTO(
            id=None,
            event_id=event_block["id"],
            event_name=event_block["name"],
            event_title=event_block["title"],
            practice_location_id=event_block["practice_location_id"],
            practice_location_name=event_block["practice_location_name"],
            event_start_time=event_block["start_time"],
            event_end_time=event_block["end_time"],
            event_update_id=event_block["event_update_id"],
            event_update_for_date=event_block["event_update_for_date"],
            slot_start_time=slot_start_time,
            slot_end_time=slot_end_time,
            visit_type=visit_type,
            visit_type_duration=visit_type_duration,
        )
