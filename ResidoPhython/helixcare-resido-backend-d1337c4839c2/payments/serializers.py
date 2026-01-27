import base64
import datetime

from django.utils.timezone import now
from rest_framework import serializers
from django.db import transaction
from django.db.models import Sum, Count
from rest_framework.exceptions import ValidationError

from common.stores.key import key_store
from common.utils.logging import logger
from common.errors import ERROR_DETAILS
from payments.managers.bill.refund.request import BillRefundRequestManager
from payments.managers.bill.core import BillManager
from payments.utils import decrypt_data_using_pvt_key
from payments.models import (
    Bill,
    BillBreakDown,
    SavedAccount,
    SavedCard,
    BillSummary,
    Payment,
    BreakdownDiscount,
    BreakdownAdjustment,
    BreakdownWriteoff,
    TypeOfService,
    TaxPerState,
    Category,
    SubCategory,
    Discount,
    PaymentPlan,
    BillAdjustment,
    BillDiscount,
    BillWriteoff,
    BillPaymentPlan,
    WriteOff,
    Adjustment,
    BillRefundRequest,
    BillCancellationCodeComposition,
)
from residents.models import Resident
from staff.models import HelixStaff
from helixauth.models import Policy
from lookup.fields import BaseSerializer
from locations.models import Location
from locations.serializers import LocationSerializer
from residents.serializers import ResidentFamilySerializer
from staff.serializers import StaffMinDetailSerializer
from payments.managers.calculator.discounts import DiscountCalculator
from payments.managers.calculator.breakdown import BreakdownCalculator
from payments.managers.calculator.bill import BillCalculator
from payments.payment_constants import (
    TransactionMethod,
    REFUNDABLE_BILL_STATUSES,
    RefundType,
    REFUND_TRANSACTION_METHODS,
    TransactionType,
    PARENT_MANDATED_REFUND_METHODS,
)
from helixauth.serializers import PolicyDetailSerializer
from payments.managers.calculator.adjustment import AdjustmentCalculator
from payments.managers.calculator.writeoff import WriteoffCalculator


class CategoryListSerializer(BaseSerializer):
    class Meta:
        model = Category
        exclude = [
            "version",
        ]


class SubCategoryListSerializer(BaseSerializer):
    category = CategoryListSerializer(read_only=True)

    class Meta:
        model = SubCategory
        exclude = [
            "version",
        ]


class TypeOfServiceSerializer(BaseSerializer):
    sub_category = SubCategoryListSerializer(read_only=True)
    sub_category_id = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(), write_only=True, source="sub_category"
    )

    class Meta:
        model = TypeOfService
        exclude = [
            "version",
        ]

    def validate(self, data):
        name = data.get("name")
        sub_category = data.get("sub_category")

        if name and sub_category:
            qs = TypeOfService.objects.filter(name=name, sub_category=sub_category)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    code="duplicate_name",
                    detail=ERROR_DETAILS["duplicate_name"].format(
                        field="Service", field_name=name
                    ),
                )
        return data


class BillAdjustmentSerializer(BaseSerializer):
    adj_obj_id = serializers.PrimaryKeyRelatedField(
        source="adj_obj", queryset=Adjustment.objects.all(), write_only=True
    )
    bill = serializers.PrimaryKeyRelatedField(
        queryset=Bill.objects.all(), required=False
    )

    class Meta:
        model = BillAdjustment
        read_only_fields = [
            "amount",
        ]
        exclude = [
            "version",
        ]

    def create(self, validated_data):
        manager = AdjustmentCalculator(
            adj_obj=validated_data.get("adj_obj"),
            amount=float(validated_data.get("bill").total_charges.amount),
        )
        validated_data["value"] = validated_data.get("adj_obj").value
        validated_data["amount"] = manager.calculate_adjustment()
        validated_data["name"] = validated_data.get("adj_obj").name
        validated_data["type_of_adjustment"] = validated_data.get(
            "adj_obj"
        ).type_of_adjustment
        validated_data["max_upto"] = (
            validated_data.get("adj_obj").max_upto.amount
            if validated_data.get("adj_obj").max_upto
            else None
        )
        validated_data["max_upto_currency"] = (
            validated_data.get("adj_obj").max_upto.currency
            if validated_data.get("adj_obj").max_upto
            else None
        )
        return super().create(validated_data)


class BreakdownAdjustmentSerializer(BaseSerializer):
    adj_obj_id = serializers.PrimaryKeyRelatedField(
        source="adj_obj", queryset=Adjustment.objects.all(), write_only=True
    )
    breakdown = serializers.PrimaryKeyRelatedField(
        queryset=BillBreakDown.objects.all(), required=False
    )

    class Meta:
        model = BreakdownAdjustment
        read_only_fields = [
            "amount",
        ]
        exclude = [
            "version",
        ]

    def create(self, validated_data):
        manager = AdjustmentCalculator(
            adj_obj=validated_data.get("adj_obj"),
            amount=float(validated_data.get("breakdown").sub_total.amount),
        )
        validated_data["value"] = validated_data.get("adj_obj").value
        validated_data["amount"] = manager.calculate_adjustment()
        validated_data["name"] = validated_data.get("adj_obj").name
        validated_data["type_of_adjustment"] = validated_data.get(
            "adj_obj"
        ).type_of_adjustment
        validated_data["max_upto"] = (
            validated_data.get("adj_obj").max_upto.amount
            if validated_data.get("adj_obj").max_upto
            else None
        )
        validated_data["max_upto_currency"] = (
            validated_data.get("adj_obj").max_upto.currency
            if validated_data.get("adj_obj").max_upto
            else None
        )
        return super().create(validated_data)


class BillDiscountSerializer(BaseSerializer):
    discount_id = serializers.PrimaryKeyRelatedField(
        source="discount", queryset=Discount.objects.all(), write_only=True
    )
    bill = serializers.PrimaryKeyRelatedField(
        queryset=Bill.objects.all(), required=False
    )

    class Meta:
        model = BillDiscount
        exclude = [
            "version",
        ]
        read_only_fields = [
            "name",
            "value",
            "discount",
        ]

    def create(self, validated_data):
        manager = DiscountCalculator(
            discount_obj=validated_data.get("discount"),
            amount=float(validated_data.get("bill").total_charges.amount),
        )
        validated_data["value"] = validated_data.get("discount").value
        validated_data["amount"] = manager.calculate_discount()
        validated_data["name"] = validated_data.get("discount").name
        validated_data["type_of_discount"] = validated_data.get(
            "discount"
        ).type_of_discount
        validated_data["max_upto"] = (
            validated_data.get("discount").max_upto.amount
            if validated_data.get("discount").max_upto
            else None
        )
        validated_data["max_upto_currency"] = (
            validated_data.get("discount").max_upto.currency
            if validated_data.get("discount").max_upto
            else None
        )
        return super().create(validated_data)


class BreakdownDiscountSerializer(BaseSerializer):
    discount_id = serializers.PrimaryKeyRelatedField(
        source="discount", queryset=Discount.objects.all(), write_only=True
    )
    breakdown = serializers.PrimaryKeyRelatedField(
        queryset=BillBreakDown.objects.all(), required=False
    )

    class Meta:
        model = BreakdownDiscount
        exclude = [
            "version",
        ]
        read_only_fields = [
            "name",
            "value",
            "amount",
            "discount",
        ]

    def create(self, validated_data):
        sub_total = (
            float(validated_data.get("breakdown").type_of_service_amount.amount)
            * validated_data.get("breakdown").quantity
        )
        manager = DiscountCalculator(
            discount_obj=validated_data.get("discount"),
            amount=float(sub_total),
        )
        validated_data["value"] = validated_data.get("discount").value
        validated_data["amount"] = manager.calculate_discount()
        if validated_data.get("discount") is not None:
            validated_data["name"] = validated_data.get("discount").name
            max_upto = validated_data.get("discount").max_upto
            if max_upto is not None and (
                hasattr(max_upto, "currency") and hasattr(max_upto, "amount")
            ):
                validated_data["max_upto_currency"] = max_upto.currency
                validated_data["max_upto"] = max_upto.amount
            validated_data["type_of_discount"] = validated_data.get(
                "discount"
            ).type_of_discount
        return super().create(validated_data)


class BillWriteoffSerializer(BaseSerializer):
    write_off_obj_id = serializers.PrimaryKeyRelatedField(
        source="write_off_obj", queryset=WriteOff.objects.all(), write_only=True
    )
    bill = serializers.PrimaryKeyRelatedField(
        queryset=Bill.objects.all(), required=False
    )

    class Meta:
        model = BillWriteoff
        read_only_fields = [
            "amount",
        ]
        exclude = [
            "version",
        ]

    def create(self, validated_data):
        manager = WriteoffCalculator(
            writeoff_obj=validated_data.get("write_off_obj"),
            amount=float(validated_data.get("bill").total_charges.amount),
        )
        validated_data["value"] = validated_data.get("write_off_obj").value
        validated_data["amount"] = manager.calculate_writeoff()
        validated_data["name"] = validated_data.get("write_off_obj").name
        validated_data["type_of_writeoff"] = validated_data.get(
            "write_off_obj"
        ).type_of_writeoff
        validated_data["max_upto"] = (
            validated_data.get("write_off_obj").max_upto.amount
            if validated_data.get("write_off_obj").max_upto
            else None
        )
        validated_data["max_upto_currency"] = (
            validated_data.get("write_off_obj").max_upto.currency
            if validated_data.get("write_off_obj").max_upto
            else None
        )
        return super().create(validated_data)


class BreakdownWriteoffSerializer(BaseSerializer):
    write_off_obj_id = serializers.PrimaryKeyRelatedField(
        source="write_off_obj", queryset=WriteOff.objects.all(), write_only=True
    )
    breakdown = serializers.PrimaryKeyRelatedField(
        queryset=BillBreakDown.objects.all(), required=False
    )

    class Meta:
        model = BreakdownWriteoff
        read_only_fields = [
            "amount",
        ]
        exclude = [
            "version",
        ]

    def create(self, validated_data):
        manager = WriteoffCalculator(
            writeoff_obj=validated_data.get("write_off_obj"),
            amount=float(validated_data.get("breakdown").sub_total.amount),
        )
        validated_data["value"] = validated_data.get("write_off_obj").value
        validated_data["amount"] = manager.calculate_writeoff()
        validated_data["name"] = validated_data.get("write_off_obj").name
        validated_data["type_of_writeoff"] = validated_data.get(
            "write_off_obj"
        ).type_of_writeoff
        validated_data["max_upto"] = (
            validated_data.get("write_off_obj").max_upto.amount
            if validated_data.get("write_off_obj").max_upto
            else None
        )
        validated_data["max_upto_currency"] = (
            validated_data.get("write_off_obj").max_upto.currency
            if validated_data.get("write_off_obj").max_upto
            else None
        )
        return super().create(validated_data)


class BillBreakDownSerializer(BaseSerializer):
    bill = serializers.PrimaryKeyRelatedField(
        queryset=Bill.objects.all(),
        write_only=True,
        required=False,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        source="category",
    )
    type_of_service_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeOfService.objects.all(),
        write_only=True,
        required=False,
        source="type_of_service",
    )
    category = CategoryListSerializer(read_only=True)
    type_of_service = TypeOfServiceSerializer(read_only=True)
    adjustments = BreakdownAdjustmentSerializer(many=True)
    discounts = BreakdownDiscountSerializer(many=True)
    writeoffs = BreakdownWriteoffSerializer(many=True)
    practice_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        write_only=True,
        required=False,
        source="practice_location",
    )

    class Meta:
        model = BillBreakDown
        fields = [
            "id",
            "date",
            "category",
            "type_of_service",
            "description",
            "quantity",
            "discounts",
            "adjustments",
            "writeoffs",
            "other_fees",
            "other_fees_currency",
            "insurance_amount",
            "insurance_amount_currency",
            "patient_amount",
            "patient_amount_currency",
            "tax",
            "tax_currency",
            "total_amount",
            "category_id",
            "type_of_service_id",
            "total_amount_currency",
            "bill",
            "category_name",
            "type_of_service_name",
            "type_of_service_amount",
            "other_fees_taxable",
            "service_start_date",
            "service_end_date",
            "practice_location_id",
        ]
        read_only_fields = [
            "patient_amount",
            "patient_amount_currency",
            "tax",
            "sub_total",
            "tax_currency",
            "total_amount",
            "total_amount_currency",
            "category_name",
            "type_of_service_name",
            "type_of_service_amount",
        ]

    def validate(self, attrs):
        validated = super().validate(attrs)
        adjustments = validated.pop("adjustments", [])
        discounts = validated.pop("discounts", [])
        writeoffs = validated.pop("writeoffs", [])
        validated["tax_state"] = (
            self.initial_data.get("state") if hasattr(self, "initial_data") else None
        )
        if not validated.get("tax_state"):
            validated["tax_state"] = (
                attrs.get("practice_location").state
                if attrs.get("practice_location")
                else None
            )
        if validated.get("quantity") == 0:
            raise serializers.ValidationError(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="quantity"),
            )
        manager = self._append_totals_data(
            data=validated,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        validated.pop("tax_state", None)
        self.context["calc_manager"] = manager
        return validated

    @staticmethod
    def _append_totals_data(data, adjustments, discounts, writeoffs):
        manager = BreakdownCalculator()
        manager.append_totals_to_data(
            data=data,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        return manager

    def create(self, validated_data):
        adjustments = self.initial_data.get("adjustments", [])
        discounts = self.initial_data.get("discounts", [])
        writeoffs = self.initial_data.get("writeoffs", [])
        validated_data["category_name"] = validated_data.get("category").name
        validated_data["type_of_service_name"] = validated_data.get(
            "type_of_service"
        ).name
        validated_data["type_of_service_amount"] = validated_data.get(
            "type_of_service"
        ).amount.amount
        validated_data["type_of_service_amount_currency"] = validated_data.get(
            "type_of_service"
        ).amount.currency
        validated_data["sub_total"] = round(
            float(validated_data.get("type_of_service").amount.amount)
            * validated_data.get("quantity"),
            2,
        )
        validated_data["sub_total_currency"] = validated_data.get(
            "type_of_service"
        ).amount.currency
        validated_data.pop("practice_location", None)
        instance = super().create(validated_data)
        manager = self.context.get("calc_manager", None) or self._append_totals_data(
            data=validated_data,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        if hasattr(manager, "disc_applied") and manager.disc_applied:
            for dis in discounts:
                dis["breakdown"] = instance.id
                srz = BreakdownDiscountSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        if hasattr(manager, "adj_applied") and manager.adj_applied:
            for dis in adjustments:
                dis["breakdown"] = instance.id
                srz = BreakdownAdjustmentSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        if hasattr(manager, "wrt_applied") and manager.wrt_applied:
            for dis in writeoffs:
                dis["breakdown"] = instance.id
                srz = BreakdownWriteoffSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        return instance


class BillSummarySerializer(BaseSerializer):
    class Meta:
        model = BillSummary
        fields = [
            "id",
            "bill",
            "title",
            "amount",
            "amount_currency",
        ]


class BillPaymentPlanMiniSerializer(BaseSerializer):
    class Meta:
        model = BillPaymentPlan
        exclude = [
            "consent_id",
            "consent_response",
            "version",
        ]


class BillDetailSerializer(BaseSerializer):
    summary = BillSummarySerializer(many=True, read_only=True)
    breakdown = BillBreakDownSerializer(many=True, required=True)
    patient = ResidentFamilySerializer(read_only=True)
    provider = StaffMinDetailSerializer(read_only=True)
    practice_location = LocationSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        required=True,
        source="patient",
    )
    practice_location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        write_only=True,
        required=True,
        source="practice_location",
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=HelixStaff.objects.all(),
        write_only=True,
        required=False,
        source="provider",
    )
    discounts = BillDiscountSerializer(many=True, required=False, default=[])
    adjustments = BillAdjustmentSerializer(many=True, required=False, default=[])
    writeoffs = BillWriteoffSerializer(many=True, required=False, default=[])
    payment_plan = BillPaymentPlanMiniSerializer(
        read_only=True, source="pp", required=False
    )
    pending_amount = serializers.SerializerMethodField(read_only=True)
    total_refundable_amount = serializers.SerializerMethodField()
    total_refunded_amount = serializers.SerializerMethodField()
    cancellation_code = serializers.SerializerMethodField(read_only=True)
    already_paid_amount_val = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            "id",
            "patient",
            "patient_id",
            "display_id",
            "service",
            "service_date",
            "statement_date",
            "total_charges",
            "total_charges_currency",
            "insurance_paid",
            "insurance_paid_currency",
            "patient_amount",
            "patient_amount_currency",
            "due_date",
            "status",
            "provider",
            "provider_id",
            "breakdown",
            "payment_plan",
            "practice_location_id",
            "practice_location",
            "summary",
            "discounts",
            "adjustments",
            "writeoffs",
            "other_discount",
            "other_adjustment",
            "other_writeoff",
            "other_tax",
            "other_discount_currency",
            "other_adjustment_currency",
            "other_writeoff_currency",
            "other_tax_currency",
            "payment_method",
            "cancellation_reason",
            "cancellation_reason_description",
            "paid_date",
            "pending_amount",
            "total_refundable_amount",
            "total_refunded_amount",
            "already_paid_amount_val",
            "cancellation_code",
            "service_start_date",
            "service_end_date",
        ]
        read_only_fields = (
            "total_charges",
            "total_charges_currency",
            "insurance_paid",
            "insurance_paid_currency",
            "patient_amount",
            "patient_amount_currency",
            "display_id",
            "other_discount",
            "other_adjustment",
            "other_writeoff",
            "other_tax",
            "other_discount_currency",
            "other_adjustment_currency",
            "other_writeoff_currency",
            "other_tax_currency",
            "pending_amount",
            "paid_date",
            "service_start_date",
            "service_end_date",
        )

    @staticmethod
    def get_cancellation_code(obj):
        return obj.cancellation_code

    @staticmethod
    def get_total_refundable_amount(obj):
        return obj.total_refundable_amount

    @staticmethod
    def get_total_refunded_amount(obj):
        return obj.total_refunded_amount

    @staticmethod
    def get_already_paid_amount_val(obj):
        return obj.already_paid_amount_val

    def upsert_breakdowns(self, instance, breakdowns):
        objs = []
        for obj in breakdowns:
            obj["bill"] = instance.id
            srz = BillBreakDownSerializer(data=obj)
            srz.is_valid(raise_exception=True)
            objs.append(srz.save())
        return objs

    @staticmethod
    def cancel_bill(instance, validated_data):
        if instance.status != "PENDING":
            raise ValidationError(
                code="invalid_status_for_cancellation",
                detail=ERROR_DETAILS["invalid_status_for_cancellation"],
            )

        instance.status = "CANCELLED"
        instance.cancellation_reason = validated_data.get("cancellation_reason")
        instance.cancellation_reason_description = validated_data.get(
            "cancellation_reason_description"
        )
        instance.save()
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        status = validated_data.get("status")
        if status == "CANCELLED":
            return self.cancel_bill(instance=instance, validated_data=validated_data)
        self._pre_save(validated_data=validated_data, old_instance=instance)
        instance = super().update(instance, validated_data)
        self._post_save(instance=instance, data=validated_data)
        return instance

    def _pre_save(self, validated_data, old_instance=None):
        brks = validated_data.pop("breakdown", [])
        adjustments = validated_data.pop("adjustments", [])
        discounts = validated_data.pop("discounts", [])
        writeoffs = validated_data.pop("writeoffs", [])
        (
            validated_data["service_start_date"],
            validated_data["service_end_date"],
        ) = self._update_service_start_end_date_from_breakdowns(breakdowns=brks)
        manager = self._append_totals_data(
            data=validated_data,
            breakdowns=brks,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        self.context["calc_manager"] = manager
        self._remove_old_instance_relations(old_instance=old_instance)

    @staticmethod
    def _update_service_start_end_date_from_breakdowns(breakdowns):
        service_start_date, service_end_date = None, None
        for obj in breakdowns:
            start = obj.get("service_start_date")
            end = obj.get("service_end_date")
            if start and (not service_start_date or start < service_start_date):
                service_start_date = start
            if end and (not service_end_date or end > service_end_date):
                service_end_date = end
        return service_start_date, service_end_date

    @staticmethod
    def _append_totals_data(data, breakdowns, adjustments, discounts, writeoffs):
        manager = BillCalculator()
        manager.append_totals_to_data(
            data=data,
            breakdowns=breakdowns,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        return manager

    @staticmethod
    def _remove_old_instance_relations(old_instance):
        if old_instance:
            [obj.delete() for obj in old_instance.breakdown.all()]
            [obj.delete() for obj in old_instance.summary.all()]
            [obj.delete() for obj in old_instance.adjustments.all()]
            [obj.delete() for obj in old_instance.discounts.all()]
            [obj.delete() for obj in old_instance.writeoffs.all()]

    def _post_save(self, instance, data):
        breakdowns = self.initial_data.get("breakdown")
        brk_objs = self.upsert_breakdowns(instance=instance, breakdowns=breakdowns)
        self.create_summary(instance=instance, breakdowns=brk_objs)
        adjustments = self.initial_data.get("adjustments", [])
        discounts = self.initial_data.get("discounts", [])
        writeoffs = self.initial_data.get("writeoffs", [])
        manager = self.context.get("calc_manager") or self._append_totals_data(
            data=data,
            breakdowns=breakdowns,
            adjustments=adjustments,
            discounts=discounts,
            writeoffs=writeoffs,
        )
        if hasattr(manager, "disc_applied") and manager.disc_applied:
            for dis in discounts:
                dis["bill"] = instance.id
                srz = BillDiscountSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        if hasattr(manager, "adj_applied") and manager.adj_applied:
            for dis in adjustments:
                dis["bill"] = instance.id
                srz = BillAdjustmentSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        if hasattr(manager, "wrt_applied") and manager.wrt_applied:
            for dis in writeoffs:
                dis["bill"] = instance.id
                srz = BillWriteoffSerializer(data=dis)
                srz.is_valid(raise_exception=True)
                srz.save()
        return instance

    @staticmethod
    def create_summary(instance, breakdowns):
        data = BillCalculator.build_summary_data(
            instance=instance, breakdowns=breakdowns
        )
        srz = BillSummarySerializer(data=data, many=True)
        srz.is_valid(raise_exception=True)
        srz.save()

    @transaction.atomic
    def create(self, validated_data):
        self._pre_save(validated_data=validated_data)
        instance = super().create(validated_data)
        self._post_save(instance=instance, data=validated_data)
        return instance

    def get_pending_amount(self, obj):
        paid_amount = obj.payments.filter(status="COMPLETED").aggregate(
            total=Sum("amount")
        )["total"]
        paid_amount = 0 if not paid_amount else float(paid_amount)
        pending_amount = (
            float(obj.patient_amount.amount) if obj.patient_amount else 0
        ) - paid_amount
        return pending_amount


class BillMinSerializer(BaseSerializer):
    patient = ResidentFamilySerializer(read_only=True)
    provider = StaffMinDetailSerializer(read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "patient",
            "created_on",
            "display_id",
            "service",
            "service_date",
            "statement_date",
            "total_charges",
            "total_charges_currency",
            "insurance_paid",
            "insurance_paid_currency",
            "patient_amount",
            "patient_amount_currency",
            "due_date",
            "status",
            "provider",
            "paid_date",
        ]
        read_only_fields = [
            "paid_date",
        ]


class BillListSerializer(BaseSerializer):
    patient = ResidentFamilySerializer(read_only=True)
    provider = StaffMinDetailSerializer(read_only=True)
    payment_plan = BillPaymentPlanMiniSerializer(
        read_only=True, source="pp", required=False
    )
    total_refundable_amount = serializers.SerializerMethodField()
    total_refunded_amount = serializers.SerializerMethodField()
    already_paid_amount_val = serializers.SerializerMethodField()
    pending_amount = serializers.SerializerMethodField(read_only=True)
    cancellation_code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "patient",
            "created_on",
            "display_id",
            "service",
            "service_date",
            "statement_date",
            "total_charges",
            "total_charges_currency",
            "insurance_paid",
            "insurance_paid_currency",
            "patient_amount",
            "patient_amount_currency",
            "due_date",
            "status",
            "provider",
            "paid_date",
            "payment_plan",
            "total_refundable_amount",
            "total_refunded_amount",
            "already_paid_amount_val",
            "pending_amount",
            "cancellation_code",
        ]
        read_only_fields = [
            "paid_date",
        ]

    @staticmethod
    def get_already_paid_amount_val(obj):
        return obj.already_paid_amount_val

    @staticmethod
    def get_cancellation_code(obj):
        return obj.cancellation_code

    @staticmethod
    def get_total_refundable_amount(obj):
        return obj.total_refundable_amount

    @staticmethod
    def get_total_refunded_amount(obj):
        return obj.total_refunded_amount

    def get_pending_amount(self, obj):
        paid_amount = obj.payments.filter(status="COMPLETED").aggregate(
            total=Sum("amount")
        )["total"]
        paid_amount = 0 if not paid_amount else float(paid_amount)
        pending_amount = (
            float(obj.patient_amount.amount) if obj.patient_amount else 0
        ) - paid_amount
        return pending_amount


class SavedCardSerializer(BaseSerializer):
    patient_details = ResidentFamilySerializer(read_only=True)

    class Meta:
        model = SavedCard
        fields = [
            "id",
            "patient",
            "patient_details",
            "last_4_digits",
            "primary_method",
            "card_number",
            "card_type",
            "expiration_month",
            "expiration_year",
            "cardholder_name",
            "active",
            "first_name",
            "last_name",
            "middle_name",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
            "data_encrypted",
        ]
        read_only_fields = [
            "last_4_digits",
            "data_encrypted",
        ]

    def validate(self, attrs):
        if self.instance:
            attrs.pop("patient", None)
            attrs.pop("card_number", None)
        else:
            attrs["last_4_digits"] = self.validate_card_number_and_get_last_4_digits(
                attrs.get("card_number")
            )
            attrs["data_encrypted"] = True
        return super().validate(attrs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.primary_method:
            self.make_other_methods_non_primary(
                patient_id=validated_data.get("patient"), id=instance.id
            )
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.primary_method:
            self.make_other_methods_non_primary(
                patient_id=validated_data.get("patient"), id=instance.id
            )
        return instance

    def make_other_methods_non_primary(self, patient_id, id=None):
        query = SavedCard.objects.filter(patient_id=patient_id)
        if id:
            query = query.exclude(id=id)
        query.update(primary_method=False)
        query2 = SavedAccount.objects.filter(patient_id=patient_id)
        query2.update(primary_method=False)

    def validate_card_number_and_get_last_4_digits(self, data):
        try:
            return decrypt_data_using_pvt_key(
                base64.b64decode(data), key_store.tn_auth_private_key
            )[-4:]
        except Exception as e:
            logger.info(
                f"Exception while decrypting the card_number data {data}, Error: {e}"
            )
            raise serializers.ValidationError(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="card_number"),
            )


class SavedAccountSerializer(BaseSerializer):
    patient_details = ResidentFamilySerializer(read_only=True)

    class Meta:
        model = SavedAccount
        fields = [
            "id",
            "patient",
            "patient_details",
            "routing_number",
            "primary_method",
            "account_number",
            "account_type",
            "first_name",
            "last_name",
            "middle_name",
            "active",
            "first_name",
            "last_name",
            "middle_name",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
            "last_4_digits",
            "data_encrypted",
        ]
        read_only_fields = [
            "last_4_digits",
            "data_encrypted",
        ]

    def validate(self, attrs):
        account_type = attrs.get("account_type")
        if account_type in ["1", "2"] and not attrs.get("last_name"):
            raise serializers.ValidationError(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param="last_name"
                ),
            )
        if self.instance:
            attrs.pop("account_number", None)
            attrs.pop("routing_number", None)
        else:
            attrs["last_4_digits"] = self.validate_encrypted_data(
                attrs.get("account_number"), "account_number"
            )[-4:]
            self.validate_encrypted_data(attrs.get("routing_number"), "routing_number")
            attrs["data_encrypted"] = True
        return super().validate(attrs)

    @staticmethod
    def validate_encrypted_data(data, attr_name):
        try:
            return decrypt_data_using_pvt_key(
                base64.b64decode(data), key_store.tn_auth_private_key
            )
        except Exception as e:
            logger.info(
                f"Exception while decrypting the card_number data {data}, Error: {e}"
            )
            raise serializers.ValidationError(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param=attr_name),
            )

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.primary_method:
            self.make_other_methods_non_primary(
                patient_id=validated_data.get("patient"), id=instance.id
            )
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.primary_method:
            self.make_other_methods_non_primary(
                patient_id=validated_data.get("patient"), id=instance.id
            )
        return instance

    def make_other_methods_non_primary(self, patient_id, id=None):
        query = SavedAccount.objects.filter(patient_id=patient_id)
        if id:
            query = query.exclude(id=id)
        query.update(primary_method=False)
        query2 = SavedCard.objects.filter(patient_id=patient_id)
        query2.update(primary_method=False)


class PaymentSerializer(BaseSerializer):
    refundable_amount = serializers.SerializerMethodField(required=False)
    saved_card_representation = serializers.SerializerMethodField(required=False)
    saved_account_representation = serializers.SerializerMethodField(required=False)
    bill = BillMinSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "display_id",
            "bill_refund_request",
            "transaction_type",
            "parent",
            "order_id",
            "amount",
            "amount_currency",
            "refund_amount",
            "refund_amount_currency",
            "refundable_amount",
            "saved_card_representation",
            "saved_account_representation",
            "payment_method",
            "status",
            "notes",
            "transaction_id",
            "error_message",
            "bill",
            "created_on",
            "saved_card",
            "saved_account",
            "payment_method_detail",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
            "extra_data",
            "write_off",
            "adjustment",
            "gateway_status",
            "gateway_status_last_updated_on",
            "gateway_recon_last_request_id",
        ]
        read_only_fields = [
            "saved_card",
            "saved_account",
            "payment_method_detail",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
        ]

    @staticmethod
    def get_refundable_amount(obj):
        return obj.refundable_amount

    @staticmethod
    def get_saved_card_representation(obj):
        return obj.card_info

    @staticmethod
    def get_saved_account_representation(obj):
        return obj.account_info


class SubCategoryDetailSerializer(SubCategoryListSerializer):
    type_of_service = TypeOfServiceSerializer(many=True, read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source="category",
    )

    class Meta:
        model = SubCategory
        exclude = [
            "version",
        ]

    def validate(self, data):
        name = data.get("name")
        category = data.get("category")

        if name and category:
            queryset = SubCategory.objects.filter(name=name, category=category)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    code="duplicate_name",
                    detail=ERROR_DETAILS["duplicate_name"].format(
                        field="Sub-category", field_name=name
                    ),
                )
        return data


class CategoryDetailSerializer(BaseSerializer):
    sub_category = SubCategoryDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        exclude = [
            "version",
        ]


class DiscountSerializer(BaseSerializer):
    class Meta:
        model = Discount
        exclude = [
            "version",
        ]


class TaxPerStateSerializer(BaseSerializer):
    class Meta:
        model = TaxPerState
        exclude = [
            "version",
        ]


class PaymentLinkGenerationSerializer(BaseSerializer):
    link = serializers.SerializerMethodField(required=False, read_only=True)
    patient = ResidentFamilySerializer(read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"

    @staticmethod
    def get_link(obj):
        return obj.link


class PaymentPlanSerializer(BaseSerializer):
    calculation = serializers.SerializerMethodField(read_only=True, required=False)
    terms_condition = PolicyDetailSerializer(
        read_only=True, context={"pop_fields": ["versions"]}
    )
    terms_condition_id = serializers.PrimaryKeyRelatedField(
        queryset=Policy.objects.all(),
        write_only=True,
        source="terms_condition",
        required=False,
    )
    privacy_policy = PolicyDetailSerializer(
        read_only=True, context={"pop_fields": ["versions"]}
    )
    privacy_policy_id = serializers.PrimaryKeyRelatedField(
        queryset=Policy.objects.all(),
        write_only=True,
        source="privacy_policy",
        required=False,
    )

    class Meta:
        model = PaymentPlan
        exclude = [
            "version",
        ]

    def get_calculation(self, obj):
        if amount := self.context.get("request").query_params.get("amount"):
            from payments.managers.bill_pp import BillPaymentPlanManager

            state = self.context.get("request").query_params.get("state", None)
            amount = float(amount)
            (
                payable_amount_using_pp,
                emi,
                pp_interest_amount,
                pp_interest_amount_tax,
                pp_fees,
                pp_fees_tax,
            ) = BillPaymentPlanManager._calculate_charges_and_emi(
                amount=amount,
                interest_rate=obj.interest_rate or 0,
                interest_rate_taxable=obj.interest_taxable or False,
                fees=float(obj.other_fees.amount) if obj.other_fees else 0,
                fees_taxable=obj.other_fees_taxable or False,
                duration=obj.duration,
                type_of_interest=obj.type_of_interest,
                type_processing_fee=obj.type_processing_fee,
                state=state,
            )
            return {
                "fees": pp_fees,
                "interest_amount": pp_interest_amount,
                "emi": emi,
                "tax": round(pp_interest_amount_tax + pp_fees_tax, 2),
                "total_amount": payable_amount_using_pp,
            }
        return None


class BillPaymentPlanSerializer(BaseSerializer):
    bill = BillListSerializer(
        required=False, read_only=True, context={"pop_fields": ["payment_plan"]}
    )
    payment_plan = PaymentPlanSerializer(required=False, read_only=True)
    pending_amount = serializers.SerializerMethodField(read_only=True)
    pending_emis = serializers.SerializerMethodField(read_only=True)
    payment_plan = BillPaymentPlanMiniSerializer(
        read_only=True, source="pp", required=False
    )

    class Meta:
        model = BillPaymentPlan
        exclude = [
            "consent_id",
            "consent_response",
            "version",
        ]
        read_only_fields = [
            "saved_card",
            "saved_account",
            "payment_method_detail",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
        ]

    def get_pending_amount(self, obj):
        paid_amount = obj.bill.payments.filter(status="COMPLETED").aggregate(
            total=Sum("amount")
        )["total"]
        paid_amount = 0 if not paid_amount else float(paid_amount)
        pending_amount = (
            float(obj.payable_amount_using_pp.amount)
            if obj.payable_amount_using_pp
            else 0
        ) - paid_amount
        return pending_amount

    def get_pending_emis(self, obj):
        count = obj.bill.payments.filter(status="COMPLETED").aggregate(
            count=Count("amount")
        )["count"]
        count = count if not count else int(count)
        return obj.duration - count


class BillPaymentPlanDetailSerializer(BillPaymentPlanSerializer):
    bill = BillDetailSerializer(
        required=False, read_only=True, context={"pop_fields": ["payment_plan"]}
    )
    payment_plan = PaymentPlanSerializer(required=False, read_only=True)
    transactions = PaymentSerializer(source="bill__payments", read_only=True)
    upcoming_emis = serializers.SerializerMethodField(read_only=True)
    end_date = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BillPaymentPlan
        exclude = [
            "consent_id",
            "consent_response",
            "version",
        ]
        read_only_fields = [
            "saved_card",
            "saved_account",
            "payment_method_detail",
            "billing_address_1",
            "billing_address_2",
            "billing_city",
            "billing_state",
            "billing_zip",
            "billing_country",
        ]

    def get_next_emi_obj(self, obj, months_to_add):
        today = datetime.datetime.now()
        if today.day < obj.day_of_month:
            months_to_add -= 1
        emi_date = datetime.datetime(
            today.year + (today.month + months_to_add - 1) // 12,
            (today.month + months_to_add - 1) % 12 + 1,
            obj.day_of_month,
        ).strftime("%Y-%m-%d")
        return {
            "amount": float(obj.emi.amount),
            "date": emi_date,
        }

    def get_upcoming_emis(self, obj):
        if obj.status != "ACTIVE":
            return []
        pending_emis = (
            obj.duration - obj.bill.payments.filter(status="COMPLETED").count()
        )
        return [self.get_next_emi_obj(obj, i + 1) for i in range(0, pending_emis)]

    def get_end_date(self, obj):
        start_date = obj.start_date
        months_to_add = obj.duration
        return datetime.datetime(
            start_date.year + (start_date.month + months_to_add - 1) // 12,
            (start_date.month + months_to_add - 1) % 12 + 1,
            start_date.day,
        ).strftime("%Y-%m-%d")


class BulkRefundTransactionsValidator(serializers.Serializer):
    transactions = serializers.JSONField(required=True)

    @staticmethod
    def validate_back_to_source_and_cash_refunds(transactions):
        payment_ids_to_refund_request_map = {}
        for refund_transaction in transactions:
            transaction_type = refund_transaction.get("transaction_type")
            if transaction_type != TransactionType.REFUND.value:
                raise serializers.ValidationError(
                    code="invalid_transaction_type",
                    detail=ERROR_DETAILS["invalid_transaction_type"],
                )

            refund_method = refund_transaction.get("payment_method")
            if refund_method not in REFUND_TRANSACTION_METHODS:
                raise serializers.ValidationError(
                    code="invalid_refund_method",
                    detail=ERROR_DETAILS["invalid_refund_method"],
                )

            if refund_method not in PARENT_MANDATED_REFUND_METHODS:
                continue

            method_lower = refund_method.lower()
            parent_transaction_id = refund_transaction.get("parent")
            if not parent_transaction_id:
                raise serializers.ValidationError(
                    code=f"payment_missing_for_{method_lower}",
                    detail=ERROR_DETAILS[f"payment_missing_for_{method_lower}"],
                )
            payment_ids_to_refund_request_map[
                parent_transaction_id
            ] = refund_transaction.get("amount")

        payment_ids = list(payment_ids_to_refund_request_map.keys())
        payments_from_db = Payment.objects.filter(
            id__in=list(payment_ids), transaction_type=TransactionType.PAYMENT.value
        )
        payment_ids_to_refundable_amount_and_obj_map = {
            str(payment.id): (payment.refundable_amount, payment)
            for payment in payments_from_db
        }
        payment_ids_from_db = set([str(payment.id) for payment in payments_from_db])
        payment_ids = set(payment_ids)

        invalid_payment_ids = payment_ids - payment_ids_from_db

        if invalid_payment_ids:
            raise serializers.ValidationError(
                code="invalid_payment_ids",
                detail=ERROR_DETAILS["invalid_payment_ids"].format(
                    payment_ids=invalid_payment_ids
                ),
            )

        for payment_id, amount_requested in payment_ids_to_refund_request_map.items():
            refundable_amount = payment_ids_to_refundable_amount_and_obj_map.get(
                payment_id
            )[0]
            if amount_requested > refundable_amount:
                raise serializers.ValidationError(
                    code="refund_requested_for_payment_too_large",
                    detail=ERROR_DETAILS[
                        "refund_requested_for_payment_too_large"
                    ].format(payment_id=payment_id),
                )

            payment_obj = payment_ids_to_refundable_amount_and_obj_map.get(
                payment_id, [None, None]
            )[1]
            if (
                payment_obj is not None
                and payment_obj.method != TransactionMethod.CASH.value
                and payment_obj.created_on >= now() - datetime.timedelta(hours=24)
                and amount_requested < refundable_amount
            ):
                # TODO MUST make 24 hours period dynamic
                raise serializers.ValidationError(
                    code="cannot_partially_refund",
                    detail=ERROR_DETAILS["cannot_partially_refund"],
                )

    def validate(self, attrs):
        transactions = attrs.get("transactions", [])
        self.validate_back_to_source_and_cash_refunds(transactions=transactions)
        return super().validate(attrs=attrs)


class BillRefundRequestSerializer(BaseSerializer):
    refund_transactions = serializers.JSONField(write_only=True)

    class Meta:
        model = BillRefundRequest
        fields = "__all__"

    @staticmethod
    def create_refund_transactions(refund_transactions, bill_refund_id, bill_id):
        for refund_transaction in refund_transactions:
            refund_transaction["bill_refund_request"] = bill_refund_id
            refund_transaction["bill"] = bill_id

        transactions_validator = BulkRefundTransactionsValidator(
            data={"transactions": refund_transactions}
        )
        transactions_validator.is_valid(raise_exception=True)

        txn_serializer = PaymentSerializer(data=refund_transactions, many=True)
        txn_serializer.is_valid(raise_exception=True)
        return txn_serializer.save()

    @staticmethod
    def init_refund_process(bill_refund_obj):
        bill_obj = bill_refund_obj.bill
        refund_manager = BillRefundRequestManager(
            bill_refund_obj=bill_refund_obj,
            bill_refund_id=str(bill_refund_obj.id),
            bill_obj=bill_obj,
            bill_id=str(bill_obj.id),
        )
        bill_refund_obj.process_id = refund_manager.init_adhoc_refund_process()
        bill_refund_obj.save()
        return bill_refund_obj

    @staticmethod
    def get_validated_bill(bill_obj):
        if bill_obj.status not in REFUNDABLE_BILL_STATUSES:
            raise serializers.ValidationError(
                code="invalid_bill_id",
                detail=ERROR_DETAILS["invalid_bill_id"].format(
                    bill_id=str(bill_obj.id)
                ),
            )

        return bill_obj

    @staticmethod
    def get_validated_refund_params(validated_data, bill_obj):
        refund_type_in_payload = validated_data.get("refund_type")

        refund_transactions, total_refund_requested = (
            validated_data.get("refund_transactions", []),
            0,
        )
        for refund_transaction in refund_transactions:
            total_refund_requested += refund_transaction.get("amount")

        if total_refund_requested > bill_obj.total_refundable_amount:
            raise serializers.ValidationError(
                code="total_refund_requested_too_large",
                detail=ERROR_DETAILS["total_refund_requested_too_large"],
            )

        refund_type = (
            RefundType.FULL_REFUND.value
            if total_refund_requested == bill_obj.patient_amount.amount
            else RefundType.PARTIAL_REFUND.value
        )

        if refund_type_in_payload is not None and refund_type_in_payload != refund_type:
            raise serializers.ValidationError(
                code="invalid_refund_type",
                detail=ERROR_DETAILS["invalid_refund_type"].format(
                    refund_type=refund_type
                ),
            )

        return refund_type, total_refund_requested

    @staticmethod
    def update_bill_obj_on_refund_type(bill_obj, bill_refund_obj):
        bill_manager = BillManager(bill_obj=bill_obj)
        return bill_manager.update_bill_upon_refund(bill_refund_obj=bill_refund_obj)

    def create(self, validated_data):
        bill = validated_data.get("bill")
        bill_obj = self.get_validated_bill(bill_obj=bill)

        refund_type, total_refund_requested = self.get_validated_refund_params(
            validated_data=validated_data, bill_obj=bill_obj
        )

        refund_transactions = validated_data.pop("refund_transactions", [])
        validated_data["refund_type"] = refund_type
        validated_data["total_refund_requested"] = total_refund_requested

        bill_refund_obj = super().create(validated_data=validated_data)
        self.create_refund_transactions(
            refund_transactions=refund_transactions,
            bill_refund_id=str(bill_refund_obj.id),
            bill_id=str(bill_obj.id),
        )
        self.update_bill_obj_on_refund_type(
            bill_obj=bill_obj, bill_refund_obj=bill_refund_obj
        )
        return self.init_refund_process(bill_refund_obj=bill_refund_obj)

    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)
        representation["bill_display_id"] = instance.bill.display_id
        refund_transactions = instance.payment_set.all()
        refund_transactions_representation = PaymentSerializer(
            refund_transactions, many=True
        ).data
        representation["refund_transactions"] = refund_transactions_representation
        return representation


class BillCancellationCodeCompositionSerializer(BaseSerializer):
    class Meta:
        model = BillCancellationCodeComposition
        fields = "__all__"
