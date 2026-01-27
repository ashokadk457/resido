from common.utils.enum import EnumWithValueConverter


class MetricTrend(EnumWithValueConverter):
    UP = "UP"
    DOWN = "DOWN"


class MetricValueSystem(EnumWithValueConverter):
    PERCENTAGE = "PERCENTAGE"
    ABSOLUTE = "ABSOLUTE"


class Trend(EnumWithValueConverter):
    UP = "UP"
    DOWN = "DOWN"
    UNCHANGED = "UNCHANGED"
