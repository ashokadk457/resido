import random

from django.core.management.base import BaseCommand
from django.db import connection
from faker import Faker

from common.utils.logging import logger
from locations.models import (
    Property,
    Location,
    FinancialDetails,
    Partner,
    ClinicLab,
    Account,
    AccountsFacility,
    VisitTypeDuration,
)
from staff.models import HelixStaff
from symptoms.models import NUCCTaxonomy

fake = Faker()


class Command(BaseCommand):
    def generate_organization_data(self):
        labs_object_list = []
        for times in range(10):
            financial_details = FinancialDetails.objects.create_financial_details()

            organization = Property.objects.create_health_center(
                finances=financial_details
            )

            partner = Partner.objects.create_partner(organization)

            for sub_times in range(2):
                lab = ClinicLab.objects.create_lab_id()
                labs_object_list.append(lab)

            for sub_times_2 in range(3):
                lab_id = random.choices(labs_object_list)
                facility = Location.objects.create_healthcare_center(
                    lab_id=lab_id[0],
                    health_center=organization,
                    partner=partner,
                    finance=financial_details,
                )
                account = Account.objects.create_account(
                    health_center=organization, practice_location=facility
                )

                AccountsFacility.objects.create_accounts_facility(
                    health_center=organization,
                    practice_location=facility,
                    account=account,
                )

                VisitTypeDuration.objects.create_practice_visit_type_duration(
                    practice_location=facility
                )
        logger.info("Organizations created successfully")

    def generate_provider_data(self):
        provider_count = 0
        organization = Property.objects.all()

        for org in organization:
            facility = Location.objects.filter(health_center=org)

            for fac in facility:
                staff_range = random.randint(10, 15)
                logger.info("{}{}{}".format(org.name, fac.name, staff_range))
                for times in range(staff_range):
                    specialities = NUCCTaxonomy.objects.all().order_by("?").first()

                    helix_staff = HelixStaff.objects.create_helix_staff(
                        organization=org, facility=fac, specialities=specialities
                    )
                    if helix_staff:
                        provider_count += 1
        logger.info("Providers created successfully: {}".format(provider_count))

    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")
        parser.add_argument("entity_type", type=str, help="Entity Type")

    def handle(self, *args, **options):
        schema_name = options["schema"]
        arg1_value = options["entity_type"]
        connection.set_schema(schema_name)

        if arg1_value == "health_center":
            self.generate_organization_data()
        elif arg1_value == "provider":
            self.generate_provider_data()
        else:
            logger.info("Invalid parameters")

        # Reset the schema name to the default after creating the user
        connection.set_schema_to_public()
