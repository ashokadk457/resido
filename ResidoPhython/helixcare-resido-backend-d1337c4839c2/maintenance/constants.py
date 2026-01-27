from common.utils.enum import EnumWithValueConverter


class MaintenanceStatus(EnumWithValueConverter):
    OPEN = "open"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
