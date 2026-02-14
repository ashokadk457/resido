from django.core.cache import cache
from django.db import connection
from django.db.models import Manager
import django.db.models.options as options

from common.managers.model.rla import RLAManagerMixin
from common.utils.logging import logger

options.DEFAULT_NAMES = options.DEFAULT_NAMES + (
    "path_to_location",
    "path_to_resident_id",
)


class GenericModelManager(RLAManagerMixin, Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_id = None

    def all(self):
        return super().filter(deleted_by=None)

    def filter(self, *args, **kwargs):
        kwargs["deleted_by"] = None
        return super().filter(*args, **kwargs)

    def figure_out_tenant_id(self):
        self._tenant_id = self._get_tenant_id()
        if self._tenant_id:
            self._tenant_id = str(self._tenant_id)
        return self._tenant_id

    @staticmethod
    def _get_tenant_id():
        return getattr(connection.tenant, "id", None)

    def delete_from_cache(self):
        if not self.figure_out_tenant_id():
            return

        return cache.delete(key=self.model.MODEL_ALL_DATA_CACHE_KEY)

    def set_all_in_cache(self, **kwargs):
        if not self.figure_out_tenant_id():
            return

        if not hasattr(self.model, "MODEL_ALL_DATA_CACHE_KEY"):
            return

        if not self.model.MODEL_ALL_DATA_CACHE_KEY:
            return

        qs = kwargs.get("qs", None)
        if qs is None:
            qs = self.all()

        data = list(qs.values())
        cache.set(key=self.model.MODEL_ALL_DATA_CACHE_KEY, value=data)
        return data

    def refresh_cache(self):
        self.delete_from_cache()
        self.set_all_in_cache()

    def get_all_from_cache(self):
        if not self.figure_out_tenant_id():
            return

        if not hasattr(self.model, "MODEL_ALL_DATA_CACHE_KEY"):
            logger.info(f"Model {self.model.__class__.__name__} not cacheable")
            return

        data = cache.get(key=self.model.MODEL_ALL_DATA_CACHE_KEY)
        if not data:
            logger.info(
                f"Fetching all data db for {self.model.MODEL_ALL_DATA_CACHE_KEY}"
            )
            qs = self.all()
            data = self.set_all_in_cache(qs=qs)

        return data

    def filter_from_cache(self, **kwargs):
        if not self.figure_out_tenant_id():
            return

        if not hasattr(self.model, "MODEL_ALL_DATA_CACHE_KEY"):
            logger.info(f"Model {self.model.__class__.__name__} not cacheable")
            return

        all_data = self.get_all_from_cache()

        filtered_data = []
        for data in all_data:
            matching = True
            for key, value in kwargs.items():
                if key.endswith("__in"):
                    act_key = key.split("__")[0]
                    if str(data.get(act_key)) not in value:
                        matching = False
                        break
                elif str(data.get(key)) != str(value):
                    matching = False
                    break
            if matching:
                filtered_data.append(data)

        return filtered_data
