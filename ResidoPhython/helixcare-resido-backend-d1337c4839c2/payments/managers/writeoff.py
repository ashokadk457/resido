from payments.models import WriteOff
from payments.serializers_v2 import WriteOffSerializer


class WriteOffManager:
    def __init__(self, **kwargs):
        self.writeoff_obj = kwargs.get("writeoff_obj")
        self.writeoff_obj_id = (
            str(self.writeoff_obj.id)
            if self.writeoff_obj is not None
            else kwargs.get("writeoff_obj_id")
        )

    def get_serialized_writeoff_data(self):
        if self.writeoff_obj is None:
            self.writeoff_obj = self.get_writeoff_obj()

        if self.writeoff_obj is None:
            return None

        return WriteOffSerializer(self.writeoff_obj).data

    def get_writeoff_obj(self):
        self.writeoff_obj = WriteOff.objects.filter(id=self.writeoff_obj_id).first()
        return self.writeoff_obj
