from django.apps import AppConfig


class SmartLockAppConfig(AppConfig):
    """
    Smart Lock application configuration.
    Manages authentication, keys, and account management.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Smart Lock API"

    def ready(self):
        """
        App initialization
        """
        import app.auth.schema 
