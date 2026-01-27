import os

import yaml

from lookup.models import Lookup


class LookupManager:
    def populate_lookup(self):
        for filename in os.listdir("data/lookup"):
            self.populate_lookup_from_file(filename=filename)

    @staticmethod
    def populate_lookup_from_file(filename):
        with open(os.path.join("data/lookup", filename), "r") as lookup_file:
            lookup_data = yaml.load_all(lookup_file, yaml.BaseLoader)
            no_title_case_fields = ["II", "III"]
            for data in lookup_data:
                if "display_name" in data:
                    if data["value"] not in no_title_case_fields:
                        data["value"] = data["value"].title()
                    Lookup.objects.update_or_create(
                        name=data["name"], code=data["code"], defaults=data
                    )
                else:
                    if data["value"] not in no_title_case_fields:
                        data["display_name"] = data["value"].title()
                        data["value"] = data["value"].title()
                    else:
                        data["display_name"] = data["value"]
                    Lookup.objects.update_or_create(
                        name=data["name"], code=data["code"], defaults=data
                    )
