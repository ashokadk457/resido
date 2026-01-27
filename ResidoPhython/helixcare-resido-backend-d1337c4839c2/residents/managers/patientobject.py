from faker import Faker

from common.managers.model.generic import GenericModelManager
from data.utils import get_all_lookup_data

fake = Faker()


class ResidentObjectManager(GenericModelManager):
    def create_patient(
        self, organization, facility, emergency_contact, insurance, account, email
    ):
        lookup_data = get_all_lookup_data()

        data = {
            "communication_mode": [
                fake.random_element(elements=lookup_data.get("COMMUNICATION_MODE"))
            ],
            "emr_id": fake.uuid4(),
            "ext_emr_id": fake.uuid4(),
            "patient_risk": fake.random_element(elements=["Low", "Medium", "High"]),
            "employer_detail": [
                {
                    "employer_name": fake.company(),
                    "employment_status": fake.random_element(
                        elements=["Full-Time", "Part-Time"]
                    ),
                }
            ],
            "dob": "1985-11-11",
            "deceased": False,
            "deceased_date": None,
            "is_minor": fake.boolean(),
            "resp_first_name": fake.first_name(),
            "resp_last_name": fake.last_name(),
            "resp_middle_name": fake.first_name(),
            "race": fake.random_element(elements=lookup_data.get("RACE")[:50]),
            "ethnicity": fake.random_element(
                elements=lookup_data.get("ETHNICITY")[:50]
            ),
            "smoking_status": fake.random_element(
                elements=lookup_data.get("SMOKING_STATUS")[:50]
            ),
            "employment_status": fake.random_element(
                elements=lookup_data.get("OCCUPATION")[:50]
            ),
            "employer_name": fake.company(),
            "income": fake.random_element(
                elements=["<20k", "20k-50k", "50k-100k", "100k+"]
            ),
            "migration_status": fake.random_element(
                elements=lookup_data.get("IMMIGRATION_STATUS")[:50]
            ),
            "education": fake.random_element(
                elements=lookup_data.get("EDUCATION")[:50]
            ),
            "transportation": fake.random_element(
                elements=lookup_data.get("TRANSPORTATION")[:50]
            ),
            "housing_status": fake.random_element(
                elements=lookup_data.get("HOUSING_STATUS")[:50]
            ),
            "appointment_remainder": [
                fake.random_element(
                    elements=lookup_data.get("APPOINTMENT_REMINDERS")[:50]
                )
            ],
            "health_remainder": [
                fake.random_element(elements=lookup_data.get("HEALTH_REMINDERS")[:50])
            ],
            "marketing_remainder": [
                fake.random_element(
                    elements=lookup_data.get("MARKETING_REMINDERS")[:50]
                )
            ],
            "reason_for_dont_contact": fake.random_element(
                elements=lookup_data.get("REASON_DONT_CONTACT")[:50]
            ),
            "email": email,
        }

        patient = self.create(**data)
        if organization:
            patient.health_center.set([organization])
        if facility:
            patient.locations.set([facility])
        if emergency_contact:
            patient.emergencycontact_set.set([emergency_contact])
        if insurance:
            patient.insurances.set([insurance])
        if account:
            patient.acc_id.set([account])

        return patient
