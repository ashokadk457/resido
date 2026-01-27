from payments.managers.writeoff import WriteOffManager
from payments.serializers_v2 import TransactionWriteOffSerializer


class TransactionWriteOffManager:
    def __init__(self, **kwargs):
        self.transaction_obj = kwargs.get("transaction_obj")
        self.transaction_id = (
            str(self.transaction_obj.id)
            if self.transaction_obj is not None
            else kwargs.get("transaction_id")
        )
        self.writeoff_obj = kwargs.get("writeoff_obj")
        self.writeoff_obj_id = (
            str(self.writeoff_obj.id)
            if self.writeoff_obj is not None
            else kwargs.get("writeoff_obj_id")
        )
        self.transaction_writeoff_obj = kwargs.get("transaction_writeoff_obj")
        self.transaction_writeoff_obj_id = (
            str(self.transaction_writeoff_obj.id)
            if self.transaction_writeoff_obj is not None
            else kwargs.get("transaction_writeoff_obj_id")
        )

    def get_writeoff_serialized_data(self):
        writeoff_manager = WriteOffManager(
            writeoff_obj_id=self.writeoff_obj_id, writeoff_obj=self.writeoff_obj
        )
        if self.writeoff_obj is None:
            self.writeoff_obj = writeoff_manager.get_writeoff_obj()

        return writeoff_manager.get_serialized_writeoff_data()

    def get_transaction_writeoff_data(self, writeoff_serialized_data):
        return {
            "transaction": self.transaction_id,
            "write_off_obj": self.writeoff_obj_id,
            "name": writeoff_serialized_data.get("name"),
            "type_of_writeoff": None,
            "value": writeoff_serialized_data.get("value"),
            "max_upto": writeoff_serialized_data.get("max_upto"),
            "taxable": True,
            "amount": float(self.transaction_obj.amount.amount),
        }

    def create_transaction_writeoff_via_serializer(self, transaction_writeoff_data):
        serializer = TransactionWriteOffSerializer(data=transaction_writeoff_data)
        serializer.is_valid(raise_exception=True)
        self.transaction_writeoff_obj = serializer.save()
        return self.transaction_writeoff_obj

    def create_transaction_writeoff(self):
        writeoff_serialized_data = self.get_writeoff_serialized_data()
        transaction_writeoff_data = self.get_transaction_writeoff_data(
            writeoff_serialized_data=writeoff_serialized_data
        )
        return self.create_transaction_writeoff_via_serializer(
            transaction_writeoff_data=transaction_writeoff_data
        )
