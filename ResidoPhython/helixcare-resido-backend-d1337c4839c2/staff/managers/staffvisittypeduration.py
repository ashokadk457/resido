from django.db.models import Manager
from faker import Faker

from data.utils import get_all_lookup_data

fake = Faker()


class VisitTypeDurationManager(Manager):
    # TODO MUST REMOVE THIS DEPRECATED
    def create_visit_type_duration(self, helix_staff):
        lookup_data = get_all_lookup_data()
        data = {
            "visit_type": fake.random_element(elements=lookup_data.get("VISIT_TYPE")),
            "duration": fake.random_int(min=15, max=240),  # duration in minutes
        }

        visit_type_duration = self.create(**data)
        visit_type_duration.provider = helix_staff
        visit_type_duration.save()
        return visit_type_duration
