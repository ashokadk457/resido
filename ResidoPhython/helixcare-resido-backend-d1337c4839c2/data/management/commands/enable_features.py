from django.core.management.base import BaseCommand
from django.db import connection
from waffle.models import Switch


class Command(BaseCommand):
    def handle(self, *args, **options):
        schema_name = options["schema"]
        connection.set_schema(schema_name)
        switch, created = Switch.objects.get_or_create(
            name="commonwell_sync", defaults={"active": False}
        )
        connection.set_schema_to_public()

    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")
