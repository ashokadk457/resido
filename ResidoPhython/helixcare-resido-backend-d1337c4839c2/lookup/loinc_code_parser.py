from lookup.models import LoincCodes
import csv


class LoincCodeParser:
    def fetch(self):
        with open("lookup/Loinc.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                code = row["LOINC_NUM"]
                component = row["COMPONENT"]
                long_common_name = row["LONG_COMMON_NAME"]
                LoincCodes.objects.get_or_create(
                    code=code,
                    defaults={
                        "component": component,
                        "long_common_name": long_common_name,
                    },
                )
