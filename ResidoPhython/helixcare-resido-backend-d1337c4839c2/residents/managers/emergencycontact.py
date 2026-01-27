from faker import Faker

from common.managers.model.generic import GenericModelManager
from data.populate_data_utility import generate_random_middle_name
from data.utils import get_all_lookup_data

fake = Faker()


class EmergencyContactManager(GenericModelManager):
    def create_emergency_contact(self):
        lookup_data = get_all_lookup_data()

        data = {
            "first_name": fake.first_name(),
            "middle_name": generate_random_middle_name(),
            "last_name": fake.last_name(),
            "address": fake.address(),
            "address_1": fake.secondary_address(),
            "city": fake.city(),
            "state": fake.random_element(elements=lookup_data.get("STATE")),
            "country": fake.random_element(elements=lookup_data.get("COUNTRY")),
            "zipcode": fake.zipcode(),
            "home_no": fake.phone_number()[:15],
            "work_no": fake.phone_number()[:15],
            "cell_no": fake.phone_number()[:15],
            "email": [{"email": fake.email()}],
        }
        emergency_contact = self.create(**data)
        return emergency_contact
