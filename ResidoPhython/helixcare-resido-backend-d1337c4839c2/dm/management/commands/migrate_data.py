from django.core.management.base import BaseCommand
from dm.managers.dm.runner import DataMigrationRunner


class Command(BaseCommand):
    def handle(self, *args, **options):
        runner = DataMigrationRunner()
        runner.run()
