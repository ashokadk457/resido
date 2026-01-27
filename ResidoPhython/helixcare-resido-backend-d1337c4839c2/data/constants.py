from common.utils.enum import EnumWithValueConverter


class DataMigrationStatus(EnumWithValueConverter):
    IN_PROGRESS = "IN_PROGRESS"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
