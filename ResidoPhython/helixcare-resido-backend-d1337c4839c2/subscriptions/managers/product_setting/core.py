import csv

from hb_core.utils.logging import logger

from subscriptions.constants import PRODUCT_SETTINGS_FILE_PATH
from subscriptions.models.product_setting import ProductSetting


class ProductSettingManager:
    def __init__(self, **kwargs):
        self.settings_data = kwargs.get("settings_data", [])

    def is_setting_enabled(self, setting_name):
        setting_value = None
        for setting in self.settings_data:
            if setting.get("name") == setting_name:
                setting_value = setting.get("value")
                break
        return setting_value in ["true", "True", "TRUE", True]

    @classmethod
    def seed_all_possible_product_settings(cls):
        logger.info("Loading settings...")
        settings_data = list(csv.DictReader(open(PRODUCT_SETTINGS_FILE_PATH)))
        for setting in settings_data:
            _id = setting.get("id")
            ProductSetting.objects.update_or_create(id=_id, defaults=setting)
        logger.info("Loaded settings.")
