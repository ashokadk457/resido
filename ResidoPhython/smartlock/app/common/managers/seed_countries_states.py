import os
import csv

from common.models import Country, State


class CountryStateMigrationManager:
    @classmethod
    def seed_countries_and_states(cls):
        countries_path = "data/countries_and_codes.csv"
        states_path = "data/states_and_codes.csv"

        if os.path.exists(countries_path):
            with open(countries_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if not row.get("Code") or not row.get("Country"):
                        continue
                    Country.objects.update_or_create(
                        code=row["Code"].strip(),
                        defaults={
                            "name": row["Country"].strip(),
                            "is_active": True,
                        },
                    )

        country_map = {country.code: country for country in Country.objects.all()}

        if os.path.exists(states_path):
            with open(states_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                State.objects.all().delete()
                for row in reader:
                    code = row.get("country_code", "").strip()
                    name = row.get("name", "").strip()
                    if not code or not name:
                        continue

                    country = country_map.get(code)
                    if not country:
                        continue

                    State.objects.update_or_create(
                        name=name,
                        country=country,
                        defaults={
                            "state_code": row.get("state_code", "").strip(),
                            "is_active": True,
                        },
                    )
