from django.core.management.base import BaseCommand
from django.db import connection

from locations.models import Customer, Property


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("schema", type=str, help="Schema Name")

    def handle(self, *args, **options):
        schema_name = options["schema"]
        connection.set_schema(schema_name)

        customer = Customer.objects.create(name="HelixCustomer")
        Property.objects.update(customer=customer)

        connection.set_schema_to_public()
