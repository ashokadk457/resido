from scheduling.models_v2 import StaffVisitType


class StaffVisitTypeManager:
    def __init__(self, **kwargs):
        self.staff_id = kwargs.get("staff_id")
        self.visit_type_id = kwargs.get("visit_type_id")
        self.staff_vt_id = kwargs.get("staff_vt_id")
        self.staff_vt_obj = kwargs.get("staff_vt_obj")

    def upsert(self, data):
        self.staff_vt_obj, _ = StaffVisitType.objects.update_or_create(
            staff_id=data.get("staff_id"),
            visit_type_id=data.get("visit_type_id"),
            defaults=data,
        )
        return self.staff_vt_obj
