from django.apps import AppConfig


class PatientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "residents"

    def ready(self) -> None:
        import residents.signals  # noqa

        return super().ready()
