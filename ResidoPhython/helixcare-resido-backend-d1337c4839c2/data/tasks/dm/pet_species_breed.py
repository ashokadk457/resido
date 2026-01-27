from dm.tasks.dm.base import BaseDataMigrationTask
from common.managers.seed_pet_species_breeds import PetSpeciesBreedMigrationManager


class PetSpeciesBreedMigrationTask(BaseDataMigrationTask):
    def __init__(self, **kwargs):
        super(PetSpeciesBreedMigrationTask, self).__init__(**kwargs)
        self.version = 1

    def _run(self):
        PetSpeciesBreedMigrationManager.seed_pet_species_and_breeds()
