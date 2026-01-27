from payments.managers.adjustment import AdjustmentManager
from payments.serializers_v2 import TransactionAdjustmentSerializer


class TransactionAdjustmentManager:
    def __init__(self, **kwargs):
        self.transaction_obj = kwargs.get("transaction_obj")
        self.transaction_id = (
            str(self.transaction_obj.id)
            if self.transaction_obj is not None
            else kwargs.get("transaction_id")
        )
        self.adjustment_obj = kwargs.get("adjustment_obj")
        self.adjustment_obj_id = (
            str(self.adjustment_obj.id)
            if self.adjustment_obj is not None
            else kwargs.get("adjustment_obj_id")
        )
        self.transaction_adjustment_obj = kwargs.get("transaction_adjustment_obj")
        self.transaction_adjustment_obj_id = (
            str(self.transaction_adjustment_obj.id)
            if self.transaction_adjustment_obj is not None
            else kwargs.get("transaction_adjustment_obj_id")
        )

    def get_adjustment_serialized_data(self):
        adjustment_manager = AdjustmentManager(
            adjustment_obj_id=self.adjustment_obj_id, adjustment_obj=self.adjustment_obj
        )
        if self.adjustment_obj is None:
            self.adjustment_obj = adjustment_manager.get_adjustment_obj()

        return adjustment_manager.get_serialized_adjustment_data()

    def get_transaction_adjustment_data(self, adjustment_serialized_data):
        return {
            "transaction": self.transaction_id,
            "adj_obj": self.adjustment_obj_id,
            "name": adjustment_serialized_data.get("name"),
            "type_of_adjustment": None,
            "value": adjustment_serialized_data.get("value"),
            "max_upto": adjustment_serialized_data.get("max_upto"),
            "taxable": True,
            "amount": float(self.transaction_obj.amount.amount),
        }

    def create_transaction_adjustment_via_serializer(self, transaction_adjustment_data):
        serializer = TransactionAdjustmentSerializer(data=transaction_adjustment_data)
        serializer.is_valid(raise_exception=True)
        self.transaction_adjustment_obj = serializer.save()
        return self.transaction_adjustment_obj

    def create_transaction_adjustment(self):
        adjustment_serialized_data = self.get_adjustment_serialized_data()
        transaction_adjustment_data = self.get_transaction_adjustment_data(
            adjustment_serialized_data=adjustment_serialized_data
        )
        return self.create_transaction_adjustment_via_serializer(
            transaction_adjustment_data=transaction_adjustment_data
        )
