import csv
from functools import lru_cache

from waffle.models import Switch
from waffle import switch_is_active
from common.constants import FEATURE_SWITCHES_FILE_PATH
from common.utils.logging import logger


class FeatureSwitchManager:
    def __init__(self, feature_switch_name):
        self.feature_switch_name = feature_switch_name

    def is_feature_active(self, switch_name=None):
        if not switch_name:
            switch_name = self.feature_switch_name

        return self._is_feature_active(switch_name=switch_name)

    @classmethod
    @lru_cache(maxsize=512)
    def _is_feature_active(cls, switch_name):
        return switch_is_active(switch_name)

    @classmethod
    def seed_feature_switches(cls):
        logger.info("Loading all feature switches...")
        feature_switches = list(csv.DictReader(open(FEATURE_SWITCHES_FILE_PATH)))
        for feature_switch in feature_switches:
            feature = feature_switch["feature_switch_name"]
            active = feature_switch["active"]
            Switch.objects.update_or_create(
                name=feature, defaults={"name": feature, "active": active}
            )

        logger.info("Loaded all feature switches.")
