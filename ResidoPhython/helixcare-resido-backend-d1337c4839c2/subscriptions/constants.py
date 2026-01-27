from enums.framework.enum import StandardEnum
from enums.framework.item import StandardEnumItem


class ProductPlanCode(StandardEnum):
    DEVELOPMENT = "DEVELOPMENT"
    INTERNAL = "INTERNAL"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    GOLD = "GOLD"
    CUSTOM = "CUSTOM"


class ProductSettingCategory(StandardEnum):
    GENERAL = StandardEnumItem(code="GENERAL", visible_name="General")
    ADDITIONAL = StandardEnumItem(code="ADDITIONAL", visible_name="Additional")
    REGIONAL = StandardEnumItem(code="REGIONAL", visible_name="Regional")


class TierCode(StandardEnum):
    TRIAL = "TRIAL"
    LIGHT = "LIGHT"
    MEDIUM = "MEDIUM"
    HEAVY = "HEAVY"


class TierMetricCode(StandardEnum):
    VIDEO_MINUTES = "VIDEO_MINUTES"
    AUDIO_MINUTES = "AUDIO_MINUTES"


PLANS_FILE_PATH = "./data/subscription/plans.csv"
PLANS_COMPOSITIONS_FILE_PATH = "./data/subscription/plan_module_composition.csv"
PRODUCT_SETTINGS_FILE_PATH = "./data/subscription/product_settings.csv"

INDIA_GO_LIVE_PLAN_NAMES = ["RESIDO Basic Plan", "RESIDO Standard Plan"]
