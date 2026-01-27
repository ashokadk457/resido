from payments.models import Adjustment
from payments.serializers_v2 import AdjustmentSerializer


class AdjustmentManager:
    def __init__(self, **kwargs):
        self.adjustment_obj = kwargs.get("adjustment_obj")
        self.adjustment_obj_id = (
            str(self.adjustment_obj.id)
            if self.adjustment_obj is not None
            else kwargs.get("adjustment_obj_id")
        )

    def get_serialized_adjustment_data(self):
        if self.adjustment_obj is None:
            self.adjustment_obj = self.get_adjustment_obj()

        if self.adjustment_obj is None:
            return None

        return AdjustmentSerializer(self.adjustment_obj).data

    def get_adjustment_obj(self):
        self.adjustment_obj = Adjustment.objects.filter(
            id=self.adjustment_obj_id
        ).first()
        return self.adjustment_obj
