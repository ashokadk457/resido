"""
Management command to initialize the application
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Initialize the Smart Lock application"

    def add_arguments(self, parser):
        parser.add_argument(
            "--create-superuser",
            action="store_true",
            help="Create a superuser account",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("=" * 50)
        )
        self.stdout.write(
            self.style.SUCCESS("Smart Lock Application Initialization")
        )
        self.stdout.write(
            self.style.SUCCESS("=" * 50)
        )

        # Perform migrations
        self.stdout.write("Running migrations...")
        from django.core.management import call_command
        call_command("migrate")
        self.stdout.write(self.style.SUCCESS("✓ Migrations completed"))

        # Create superuser if requested
        if options["create_superuser"]:
            self.stdout.write("Creating superuser...")
            if User.objects.filter(username="admin").exists():
                self.stdout.write(
                    self.style.WARNING("Superuser 'admin' already exists")
                )
            else:
                User.objects.create_superuser(
                    username="admin",
                    email="admin@smartlock.local",
                    password="admin123"  # Change in production!
                )
                self.stdout.write(
                    self.style.SUCCESS("✓ Superuser 'admin' created")
                )

        self.stdout.write(
            self.style.SUCCESS("=" * 50)
        )
        self.stdout.write(
            self.style.SUCCESS("Initialization completed successfully!")
        )
        self.stdout.write(
            self.style.WARNING(
                "Remember to change default passwords in production"
            )
        )
