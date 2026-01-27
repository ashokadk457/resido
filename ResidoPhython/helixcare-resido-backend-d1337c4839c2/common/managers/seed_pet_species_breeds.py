import os
import csv

from common.models import PetSpecies, PetBreed


class PetSpeciesBreedMigrationManager:
    @classmethod
    def seed_pet_species_and_breeds(cls):
        species_path = "data/pet_species.csv"
        breeds_path = "data/pet_breeds.csv"

        if os.path.exists(species_path):
            with open(species_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if not row.get("code") or not row.get("name"):
                        continue
                    PetSpecies.objects.update_or_create(
                        code=row["code"].strip(),
                        defaults={
                            "name": row["name"].strip(),
                            "is_active": True,
                        },
                    )

        species_map = {species.code: species for species in PetSpecies.objects.all()}

        if os.path.exists(breeds_path):
            with open(breeds_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    species_code = row.get("species_code", "").strip()
                    code = row.get("code", "").strip()
                    name = row.get("name", "").strip()
                    if not species_code or not code or not name:
                        continue

                    species = species_map.get(species_code)
                    if not species:
                        continue

                    PetBreed.objects.update_or_create(
                        code=code,
                        species=species,
                        defaults={
                            "name": name,
                            "is_active": True,
                        },
                    )
