import traceback
from django.db.migrations.exceptions import MigrationSchemaMissing
from django_tenants.management.commands.migrate_schemas import MigrateSchemasCommand

from common.utils.logging import logger


class Command(MigrateSchemasCommand):
    def handle(self, *args, **options):
        logger.info("Migrating Schemas...")
        try:
            super(Command, self).handle(*args, **options)
        except MigrationSchemaMissing as e:
            logger.error(f"Exception occurred while running migrations: {str(e)}")
            traceback.print_exc()

        logger.info("Finished Migrations")
