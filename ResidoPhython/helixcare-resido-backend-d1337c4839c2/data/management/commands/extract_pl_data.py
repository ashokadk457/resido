import csv
import os

import pandas as pd
import psycopg2
from django.core.management.base import BaseCommand
from django.db import connection
from faker import Faker

fake = Faker()


class Command(BaseCommand):
    def fetch_data_and_write_to_csv(self, sql_query, item, csv_file):
        conn = psycopg2.connect(
            dbname=os.getenv("NPI_DB_NAME"),
            user=os.getenv("NPI_DB_USER"),
            password=os.getenv("NPI_DB_PASSWORD"),
            host=os.getenv("NPI_DB_HOST"),
            port=os.getenv("NPI_DB_PORT"),
        )

        cursor = conn.cursor()
        try:
            cursor.execute(sql_query, (item,))
        except Exception as e:
            print("Exception: ", e)
        column_names = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        print(f"Row Length for {item}: {len(rows)}")

        data = pd.DataFrame(rows, columns=column_names)

        deduplicated_df = data.drop_duplicates(
            subset=[
                "provider_first_line_business_practice_location_address",
                "provider_business_practice_location_address_city_name",
                "provider_business_practice_location_address_state_name",
                "provider_business_practice_location_address_postal_code",
            ],
            keep="last",
        )

        deduplicated_df.reset_index(drop=True, inplace=True)
        print(f"Deduplicated DF Length for {item}: {len(deduplicated_df)}")

        with open(csv_file, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(deduplicated_df.columns)
            csv_writer.writerows(deduplicated_df.values)

        print("Processed for state: ", item)

        cursor.close()
        conn.close()

    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")
        parser.add_argument("state_name", type=str, help="State Name")

    def handle(self, *args, **options):
        schema_name = options["schema"]
        state_name = options["state_name"]
        connection.set_schema(schema_name)

        csv_file = "data/" + state_name + ".csv"
        sql_query = (
            "select npi, "
            "provider_organization_name, "
            "provider_other_organization_name, "
            "provider_first_line_business_mailing_address, "
            "provider_second_line_business_mailing_address, "
            "provider_business_mailing_address_city_name, "
            "provider_business_mailing_address_state_name, "
            "provider_business_mailing_address_postal_code, "
            "provider_business_mailing_address_country_code, "
            "provider_business_mailing_address_telephone_number, "
            "provider_business_mailing_address_fax_number, "
            "provider_first_line_business_practice_location_address, "
            "provider_second_line_business_practice_location_address, "
            "provider_business_practice_location_address_city_name, "
            "provider_business_practice_location_address_state_name, "
            "provider_business_practice_location_address_postal_code, "
            "provider_business_practice_location_address_country_code, "
            "provider_business_practice_location_address_telephone_number, "
            "provider_business_practice_location_address_fax_number, "
            "authorized_official_last_name, "
            "authorized_official_first_name, "
            "authorized_official_middle_name, "
            "authorized_official_title_or_position, "
            "authorized_official_telephone_number, "
            "healthcare_provider_taxonomy_code_1, "
            "provider_license_number_1, "
            "provider_license_number_state_code_1, "
            "healthcare_provider_taxonomy_code_2, "
            "provider_license_number_2, "
            "provider_license_number_state_code_2, "
            "healthcare_provider_taxonomy_code_3, "
            "provider_license_number_3, "
            "provider_license_number_state_code_3, "
            "healthcare_provider_taxonomy_code_4, "
            "provider_license_number_4, "
            "provider_license_number_state_code_4, "
            "healthcare_provider_taxonomy_code_5, "
            "provider_license_number_5, "
            "provider_license_number_state_code_5, "
            "healthcare_provider_taxonomy_code_6, "
            "provider_license_number_6, "
            "provider_license_number_state_code_6, "
            "healthcare_provider_taxonomy_code_7, "
            "provider_license_number_7, "
            "provider_license_number_state_code_7, "
            "healthcare_provider_taxonomy_code_8, "
            "provider_license_number_8, "
            "provider_license_number_state_code_8, "
            "healthcare_provider_taxonomy_code_9, "
            "provider_license_number_9, "
            "provider_license_number_state_code_9, "
            "healthcare_provider_taxonomy_code_10, "
            "provider_license_number_10, "
            "provider_license_number_state_code_10, "
            "healthcare_provider_taxonomy_code_11, "
            "provider_license_number_11, "
            "provider_license_number_state_code_11, "
            "healthcare_provider_taxonomy_code_12, "
            "provider_license_number_12, "
            "provider_license_number_state_code_12, "
            "healthcare_provider_taxonomy_code_13, "
            "provider_license_number_13, "
            "provider_license_number_state_code_13, "
            "healthcare_provider_taxonomy_code_14, "
            "provider_license_number_14, "
            "provider_license_number_state_code_14, "
            "healthcare_provider_taxonomy_code_15, "
            "provider_license_number_15, "
            "provider_license_number_state_code_15 "
            "from helix_npi_data_dict where entity_type_code = '2' "
            "and provider_business_practice_location_address_state_name = %s "
            "order by npi;"
        )

        self.fetch_data_and_write_to_csv(sql_query, state_name, csv_file)

        # Reset the schema name to the default after creating the user
        connection.set_schema_to_public()
