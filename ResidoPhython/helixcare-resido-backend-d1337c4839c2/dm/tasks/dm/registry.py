from common.utils.enum import EnumWithValueConverter
from data.tasks.dm.aptask import AsyncPeriodicTasksDataMigration
from data.tasks.dm.country_state import CountryStateMigrationTask

# from data.tasks.dm.codecomp import BillCancellationCodeCompositionMigrationTask
from data.tasks.dm.lookups import LookupsMigrationTask
from data.tasks.dm.modules import ModulesMigrationTask
from data.tasks.dm.notification import NotificationSettingMigrationTask
from data.tasks.dm.permissions import PermissionsMigrationTask
from data.tasks.dm.subscription import (
    PlansDataMigrationTask,
    SubscriptionPlansMigrationTask,
)
from data.tasks.dm.plan_composition import PlanModuleCompositionDataMigrationTask
from data.tasks.dm.switch import FeatureSwitchMigrationTask
from data.tasks.dm.pet_species_breed import PetSpeciesBreedMigrationTask


class DataMigrationTask(EnumWithValueConverter):
    FEATURE_SWITCHES_MIGRATION_TASK = FeatureSwitchMigrationTask
    COUNTRY_STATE_MIGRATION_TASK = CountryStateMigrationTask
    LOOKUPS_MIGRATION_TASK = LookupsMigrationTask
    MODULES_MIGRATION_TASK = ModulesMigrationTask
    PERMISSION_MIGRATION_TASK = PermissionsMigrationTask
    NOTIFICATION_SETTINGS_MIGRATION_TASK = NotificationSettingMigrationTask
    PLANS_DATA_MIGRATION_TASK = PlansDataMigrationTask
    PLAN_MODULE_COMPOSITION_DATA_MIGRATION_TASK = PlanModuleCompositionDataMigrationTask
    # Backward compatibility
    SUBSCRIPTION_PLANS_MIGRATION_TASK = SubscriptionPlansMigrationTask
    # BILL_CANCELLATION_CODE_COMPOSITION_MIGRATION_TASK = (
    #     BillCancellationCodeCompositionMigrationTask
    # )
    ASYNC_PERIODIC_TASKS_MIGRATION_TASK = AsyncPeriodicTasksDataMigration
    PET_SPECIES_BREED_MIGRATION_TASK = PetSpeciesBreedMigrationTask

    @classmethod
    def choices(cls):
        values = cls.values()
        return tuple([(_class.__name__, _class.__name__) for _class in values])
