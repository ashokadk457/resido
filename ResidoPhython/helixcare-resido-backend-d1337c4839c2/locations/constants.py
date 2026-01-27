from common.utils.enum import EnumWithValueConverter


class UnitType(EnumWithValueConverter):
    OWNED = "owned"
    RENTAL = "rental"


class UnitStatus(EnumWithValueConverter):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    MOVE_OUT_SCHEDULED = "move_out_scheduled"
    UNDER_MAINTENANCE = "under_maintenance"


class SlotAvailabilityType(EnumWithValueConverter):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    VIP_ONLY = "vip_only"
    ELECTRIC_CHARGING_ONLY = "electric_charging_only"
    DISABLED_ACCESS_ONLY = "disabled_access_only"
    OUT_OF_SERVICE = "out_of_service"


class SlotType(EnumWithValueConverter):
    LARGE = "large"
    EV = "ev"
    COMPACT = "compact"
    BIKE = "bike"
