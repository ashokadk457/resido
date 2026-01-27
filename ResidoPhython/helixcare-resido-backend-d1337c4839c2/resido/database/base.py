from django.contrib.gis.db.backends.postgis.base import (
    DatabaseWrapper as OriginalPostGisDatabaseWrapper,
)
from django_tenants.utils import get_public_schema_name


class DatabaseWrapper(OriginalPostGisDatabaseWrapper):
    """
    This database wrapper explicitly sets the search path when preparing the database, as
    multi-schema environments (like with Django-tenants) can cause issues with the PostGis
    backend.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PUBLIC_SCHEMA_NAME = get_public_schema_name()

    def prepare_database(self):
        # Check that postgis extension is installed.
        with self.cursor() as cursor:
            cursor.execute("SET search_path = %s", params=[self.PUBLIC_SCHEMA_NAME])
            cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
