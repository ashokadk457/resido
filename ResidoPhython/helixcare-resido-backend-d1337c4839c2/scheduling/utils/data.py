import copy
import random

from dateutil.parser import parse
from django.db.models import Q

from lookup.models import Lookup
from staff.models import HelixStaff
from scheduling.constants import (
    early_morning_details,
    morning_details,
    afternoon_details,
    evening_details,
    time_details,
    early_morning_start_times_1st_half,
    early_morning_end_time_1st_half,
    early_morning_start_times_2nd_half,
    early_morning_end_time_2nd_half,
    early_morning_break_start_time,
    early_morning_break_end_time,
    morning_start_times_1st_half,
    morning_end_time_1st_half,
    morning_start_times_2nd_half,
    morning_end_time_2nd_half,
    morning_break_start_time,
    morning_break_end_time,
    afternoon_start_times_1st_half,
    afternoon_end_time_1st_half,
    afternoon_start_times_2nd_half,
    afternoon_break_start_time,
    afternoon_break_end_time,
    afternoon_end_time_2nd_half,
    evening_start_times_1st_half,
    evening_end_time_1st_half,
    evening_start_times_2nd_half,
    evening_end_time_2nd_half,
    evening_break_start_time,
    evening_break_end_time,
    weekdays,
)
from scheduling.models import StaffEvent, StaffWorkingHour
from scheduling.serializers import (
    FullScheduleTemplateSerializer,
    FullStaffWorkingHourSerializer,
)


def get_all_visit_types_codes():
    all_visit_types = [
        c.get("code") for c in Lookup.objects.filter(name="VISIT_TYPE").values("code")
    ]
    return all_visit_types


def create_staff_working_hour_schedule_template():
    # right
    wh_templates = [
        {
            "name": "Staff WH Early Morning",
            "description": "Starts before 10am",
            "template_category": "working_hours",
            "template_type": "weekly",
            "applicable_start_date": "2024-01-01",
            "applicable_end_date": None,
            "active": True,
            "details": early_morning_details,
        },
        {
            "name": "Staff WH Morning",
            "description": "Starts before 12pm",
            "template_category": "working_hours",
            "template_type": "weekly",
            "applicable_start_date": "2024-01-01",
            "applicable_end_date": None,
            "active": True,
            "details": morning_details,
        },
        {
            "name": "Staff WH Afternoon",
            "description": "Starts after 12pm",
            "template_category": "working_hours",
            "template_type": "weekly",
            "applicable_start_date": "2024-01-01",
            "applicable_end_date": None,
            "active": True,
            "details": afternoon_details,
        },
        {
            "name": "Staff WH Evening",
            "description": "Starts after 5pm",
            "template_category": "working_hours",
            "template_type": "weekly",
            "applicable_start_date": "2024-01-01",
            "applicable_end_date": None,
            "active": True,
            "details": evening_details,
        },
    ]

    serializer = FullScheduleTemplateSerializer(data=wh_templates, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()


def create_staff_working_hours(all_staffs=None):
    # right
    for staff in all_staffs:
        for location in staff.locations.all():
            if StaffWorkingHour.objects.filter(
                staff_id=staff.id, practice_location_id=location.id
            ).first():
                continue
            details = copy.deepcopy(random.choice(time_details))
            for detail in details:
                detail.pop("schedule_template", None)
                detail["staff_workinghour"] = None

            working_hour = {
                "staff": staff.id,
                "practice_location": staff.primary_location.id,
                "applicable_start_date": "2024-01-01",
                "details": details,
            }
            serializer = FullStaffWorkingHourSerializer(data=working_hour)
            serializer.is_valid(raise_exception=True)
            serializer.save()


def populate_all_event(all_staffs=None):
    from tqdm import tqdm

    all_visit_types = get_all_visit_types_codes()
    vt_minus_np_phy = [vt for vt in all_visit_types if vt != "NP_PHY"]
    if not all_staffs:
        all_staffs = HelixStaff.objects.filter(~Q(primary_location=None))
    events = []
    for staff_obj in all_staffs:
        for location in staff_obj.locations.all():
            if staff_obj.starts_in_early_morning:
                start_time = random.choice(early_morning_start_times_1st_half)
                end_time = random.choice(early_morning_end_time_1st_half)
                start_time_2nd_half = random.choice(early_morning_start_times_2nd_half)
                end_time_2nd_half = random.choice(early_morning_end_time_2nd_half)
                start_time_break = random.choice(early_morning_break_start_time)
                end_time_break = random.choice(early_morning_break_end_time)
            elif staff_obj.starts_in_morning:
                start_time = random.choice(morning_start_times_1st_half)
                end_time = random.choice(morning_end_time_1st_half)
                start_time_2nd_half = random.choice(morning_start_times_2nd_half)
                end_time_2nd_half = random.choice(morning_end_time_2nd_half)
                start_time_break = random.choice(morning_break_start_time)
                end_time_break = random.choice(morning_break_end_time)
            elif staff_obj.starts_in_afternoon:
                start_time = random.choice(afternoon_start_times_1st_half)
                end_time = random.choice(afternoon_end_time_1st_half)
                start_time_2nd_half = random.choice(afternoon_start_times_2nd_half)
                end_time_2nd_half = random.choice(afternoon_end_time_2nd_half)
                start_time_break = random.choice(afternoon_break_start_time)
                end_time_break = random.choice(afternoon_break_end_time)
            elif staff_obj.starts_in_evening:
                start_time = random.choice(evening_start_times_1st_half)
                end_time = random.choice(evening_end_time_1st_half)
                start_time_2nd_half = random.choice(evening_start_times_2nd_half)
                end_time_2nd_half = random.choice(evening_end_time_2nd_half)
                start_time_break = random.choice(evening_break_start_time)
                end_time_break = random.choice(evening_break_end_time)

            event = StaffEvent(
                name="Available for appointment - 1st Half",
                title="AVAILABLE",
                staff=staff_obj,
                practice_location=location,
                start_date=parse("2024-02-01").date(),
                start_time=start_time,
                end_time=end_time,
                repeating=True,
                repeat_interval=1,
                repeat_frequency="week",
                repeat_on_days_of_week=random.sample(weekdays, random.choice([4, 5])),
                visit_types=["NP_PHY"]
                + random.sample(vt_minus_np_phy, random.choice([15, 20, 23])),
            )
            event2nd_half = StaffEvent(
                name="Available for appointment - 2nd Half",
                title="AVAILABLE",
                staff=staff_obj,
                practice_location=location,
                start_date=parse("2024-02-01").date(),
                start_time=start_time_2nd_half,
                end_time=end_time_2nd_half,
                repeating=True,
                repeat_interval=1,
                repeat_frequency="week",
                repeat_on_days_of_week=random.sample(weekdays, random.choice([4, 5])),
                visit_types=["NP_PHY"]
                + random.sample(vt_minus_np_phy, random.choice([15, 20, 23])),
            )
            event_break = StaffEvent(
                name="Break",
                title="BUSY",
                staff=staff_obj,
                practice_location=location,
                start_date=parse("2024-02-01").date(),
                start_time=start_time_break,
                end_time=end_time_break,
                repeating=True,
                repeat_interval=1,
                repeat_frequency="day",
            )
            events.append(event)
            events.append(event2nd_half)
            events.append(event_break)

    for event in tqdm(events):
        event.save()
    # StaffEvent.objects.bulk_create(events)
