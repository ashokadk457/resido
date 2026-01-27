from django.core.management.base import BaseCommand
from django.db import connection

from lookup.managers.lookup import LookupManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")

    def handle(self, *args, **options):
        schema_name = options["schema"]
        connection.set_schema(schema_name)

        LookupManager().populate_lookup()

        # Reset the schema name to the default after creating the user
        connection.set_schema_to_public()
