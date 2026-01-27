from datetime import timedelta, datetime, time, date, timezone

from scheduling.dto.slot import SlotDTO


class DateTimeUtils:
    @staticmethod
    def get_iso_datetime_from_now(offset_in_seconds: int) -> str:
        sometime_later = datetime.now(tz=timezone.utc) + timedelta(
            seconds=offset_in_seconds
        )
        return sometime_later.isoformat()[:-7].split(".")[0]

    @staticmethod
    def custom_time_parser(time_str):
        hour, minute, second = map(int, time_str.split(":"))
        return time(hour=hour, minute=minute, second=second)

    @staticmethod
    def custom_datetime_parser(datetime_str):
        year, month, day, hour, minute, second = map(
            int, datetime_str.replace(" ", "-").replace(":", "-").split("-")
        )
        return datetime(year, month, day, hour, minute, second)

    @staticmethod
    def custom_date_parser(date_str):
        year, month, day = map(int, date_str.split("-"))
        return date(year, month, day)

    @classmethod
    def get_largest_date_less_than_or_equal_to(cls, dates_map, from_date_obj):
        dates_arr = dates_map.keys()
        largest_date = None
        for d in dates_arr:
            # date_obj = datetime.strptime(d, "%Y-%m-%d")
            date_obj = cls.custom_date_parser(d)
            if date_obj <= from_date_obj and (
                largest_date is None or (largest_date and date_obj > largest_date)
            ):
                largest_date = date_obj

        if largest_date is None:
            return largest_date

        return largest_date.isoformat()

    @staticmethod
    def generate_slots(
        event_block,
        block_start_time,
        block_end_time,
        slot_duration,
        visit_type,
        visit_type_duration,
    ):
        current_time = block_start_time
        slot_dtos = []
        slot_duration = timedelta(minutes=slot_duration)
        while current_time < block_end_time:
            slot_dto = SlotDTO.init(
                event_block=event_block,
                slot_start_time=current_time,
                slot_end_time=current_time + slot_duration,
                visit_type=visit_type,
                visit_type_duration=visit_type_duration,
            )
            slot_dtos.append(slot_dto)
            current_time += slot_duration

        return slot_dtos
