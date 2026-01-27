from faker import Faker

from data.utils import get_all_lookup_data
from common.managers.model.generic import GenericModelManager
from data.populate_data_utility import generate_random_middle_name, get_lat_long_point


fake = Faker()


class PracticeLocationObjectManager(GenericModelManager):
    def create_healthcare_center(self, lab_id, health_center, partner, finance):
        lookup_data = get_all_lookup_data()

        data = {
            "npi": fake.pyint(min_value=100000, max_value=999999),
            "group_npi": fake.pyint(min_value=100000, max_value=999999),
            "name": fake.company(),
            "url": fake.url(),
            "image": None,
            "payable_to": fake.company(),
            "address": fake.address(),
            "address_1": fake.secondary_address(),
            "city": fake.city(),
            "state": fake.random_element(elements=lookup_data.get("STATE")),
            "country": fake.random_element(elements=lookup_data.get("COUNTRY")),
            "contact_prefix": fake.random_element(elements=lookup_data.get("PREFIX")),
            "contact_first_name": fake.first_name(),
            "contact_mi": generate_random_middle_name(),
            "contact_last_name": fake.last_name(),
            "contact_suffix": fake.random_element(elements=lookup_data.get("SUFFIX")),
            "zipcode": fake.zipcode(),
            "latlng": get_lat_long_point(),
            "work_phone": fake.phone_number()[:10],
            "cell_phone": fake.phone_number()[:10],
            "entity": fake.random_element(elements=["INT", "EXT"]),
            "direct_email": fake.email(),
            "addresses": fake.address(),
            "fax": fake.phone_number()[:10],
            "emails": [{"email": fake.email()}],
            "notes": fake.text(),
            "communication_mode": [
                fake.random_element(elements=lookup_data.get("COMMUNICATION_MODE"))
            ],
            "type": fake.random_element(elements=lookup_data.get("FACILITY_TYPE")),
            "clia_id": fake.pyint(min_value=100000, max_value=999999),
            "mammography_cert_id": fake.pyint(min_value=100000, max_value=999999),
            "sales_tax": fake.pyint(min_value=100000, max_value=999999),
            "sate_immu_id": fake.pyint(min_value=100000, max_value=999999),
            "display_id": "FAC" + str(fake.pyint(min_value=100000, max_value=999999)),
            "is_active": True,
        }
        healthcare_center = self.create(**data)
        healthcare_center.health_center = health_center
        healthcare_center.partner = partner
        healthcare_center.labs.set([lab_id])
        healthcare_center.finances.set([finance])
        healthcare_center.save()
        return healthcare_center

    def _for_current_staff(self, user, queryset):
        path_to_location = getattr(self.model._meta, "path_to_location", None)
        if not path_to_location:
            return queryset

        staff = getattr(user, "helixuser_staff", None)
        if not staff:
            return queryset

        access_level = staff.user.access_level if staff.user else "location"

        if access_level == "location":
            locations = staff.locations.all()
            return locations
        elif access_level == "health_center":
            organizations = staff.health_centers.all()
            return queryset.filter(**{"health_center__in": organizations})
        elif access_level == "customer":
            customer = staff.customers.all()
            return queryset.filter(**{"health_center__customer__in": customer})
        elif access_level == "admin":
            return self.all()

        return queryset
