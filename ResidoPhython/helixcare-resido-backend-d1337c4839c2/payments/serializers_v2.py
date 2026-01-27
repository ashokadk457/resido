from rest_framework import serializers

from lookup.fields import BaseSerializer
from payments.managers.calculator.adjustment import AdjustmentCalculator
from payments.managers.calculator.writeoff import WriteoffCalculator
from payments.models import (
    TransactionWriteOff,
    TransactionAdjustment,
    WriteOff,
    Adjustment,
)


class WriteOffSerializer(BaseSerializer):
    calculated_amount = serializers.SerializerMethodField(
        read_only=True, required=False
    )

    class Meta:
        model = WriteOff
        exclude = [
            "version",
            "max_upto_currency",
        ]

    def get_calculated_amount(self, obj):
        request = self.context.get("request")
        if request is not None:
            if amount := request.query_params.get("amount"):
                mngr = WriteoffCalculator(writeoff_obj=obj, amount=amount)
                return mngr.calculate_writeoff()
        return None


class AdjustmentSerializer(BaseSerializer):
    calculated_amount = serializers.SerializerMethodField(
        read_only=True, required=False
    )

    class Meta:
        model = Adjustment
        exclude = [
            "version",
        ]

    def get_calculated_amount(self, obj):
        request = self.context.get("request")
        if request is not None:
            if amount := request.query_params.get("amount"):
                mngr = AdjustmentCalculator(adj_obj=obj, amount=amount)
                return mngr.calculate_adjustment()
        return None


class TransactionWriteOffSerializer(BaseSerializer):
    class Meta:
        model = TransactionWriteOff
        fields = "__all__"


class TransactionAdjustmentSerializer(BaseSerializer):
    class Meta:
        model = TransactionAdjustment
        fields = "__all__"
