import json
from datetime import datetime

from django.db.models import Sum

from audit.models import GenericModel
from common.utils.general import get_display_id
from djmoney.models.fields import MoneyField
from django.db import models
from lookup.fields import LookupField
from residents.models import Resident
from payments.gateway.easypay.constants import EasyPayTxnStatus
from payments.constants import DiscountFrequencyType, DiscountApplicableType
from processflow.models import Process
from staff.models import HelixStaff
from payments.payment_constants import (
    PAYMENT_LINK_TEMPLATE_URL,
    RefundRequestStatus,
    RefundType,
    TransactionType,
    TransactionMethod,
    TransactionStatus,
    SUCCESSFUL_REFUND_REQUEST_STATUSES,
    CARD_BASED_TRANSACTION_METHODS,
    TransactionEventSource,
    PAYMENT_ORIGINALLY_DONE_STATUSES,
)
from locations.models import Location
from helixauth.models import Policy

optional = {"null": True, "blank": True}


class Category(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)


class SubCategory(GenericModel):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="sub_category"
    )
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)


class TypeOfService(GenericModel):
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, related_name="type_of_service"
    )
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    taxable = models.BooleanField(default=True)
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")


class TaxPerState(GenericModel):
    state = models.CharField(max_length=255, unique=True)
    tax_type = LookupField(max_length=50, lookup_name="TAX_TYPE")
    value = models.FloatField()
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    country = LookupField(max_length=10, lookup_name="COUNTRY")
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


class Discount(GenericModel):
    name = models.CharField(max_length=255)
    type_of_discount = LookupField(max_length=50, lookup_name="DISCOUNT_TYPE")
    value = models.FloatField()
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    active = models.BooleanField(default=True)
    start_date = models.DateField(**optional)
    end_date = models.DateField(**optional)
    frequency = models.CharField(
        choices=DiscountFrequencyType.choices(),
        max_length=30,
    )
    applicable_charges = models.CharField(
        choices=DiscountApplicableType.choices(), max_length=30, **optional
    )
    free_percentage = models.PositiveIntegerField(**optional)
    maximum_cap = models.FloatField(**optional)
    waved_fee = models.FloatField(**optional)


class SavedCard(GenericModel):
    patient = models.ForeignKey(Resident, on_delete=models.DO_NOTHING)
    card_number = models.TextField()
    last_4_digits = models.CharField(max_length=4, **optional)
    primary_method = models.BooleanField(default=False)
    card_type = LookupField(max_length=50, lookup_name="CARD_TYPES")
    expiration_month = models.IntegerField(null=True)
    expiration_year = models.IntegerField(null=True)
    cardholder_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, **optional)
    last_name = models.CharField(max_length=100, **optional)
    middle_name = models.CharField(max_length=100, **optional)
    billing_address_1 = models.CharField(max_length=100, **optional)
    billing_address_2 = models.CharField(max_length=100, **optional)
    billing_city = models.CharField(max_length=100, **optional)
    billing_state = models.CharField(max_length=100, **optional)
    billing_zip = models.CharField(max_length=100, **optional)
    billing_country = models.CharField(max_length=100, **optional)
    data_encrypted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        path_to_resident_id = "patient__id"

    @property
    def masked_number(self):
        if not self.last_4_digits:
            return ""
        return f"**** **** **** {self.last_4_digits}"

    @property
    def user_representation(self):
        representation = "Card- "
        if self.card_type:
            representation = f"{self.card_type}- "
        if self.last_4_digits:
            representation = f"{representation}{self.masked_number}"
        return representation

    def __str__(self):
        return self.user_representation


class SavedAccount(GenericModel):
    ACC_TYPE = [
        ("1", "Personal Checking"),
        ("2", "Personal Saving"),
        ("3", "Business Checking"),
        ("4", "Business Saving"),
    ]
    patient = models.ForeignKey(Resident, on_delete=models.DO_NOTHING)
    routing_number = models.TextField()
    account_number = models.TextField()
    last_4_digits = models.CharField(max_length=255, **optional)
    account_type = models.CharField(max_length=20, choices=ACC_TYPE, default="1")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, **optional)
    middle_name = models.CharField(max_length=100, **optional)
    billing_address_1 = models.CharField(max_length=100, **optional)
    billing_address_2 = models.CharField(max_length=100, **optional)
    billing_city = models.CharField(max_length=100, **optional)
    billing_state = models.CharField(max_length=100, **optional)
    billing_zip = models.CharField(max_length=100, **optional)
    billing_country = models.CharField(max_length=100, **optional)
    primary_method = models.BooleanField(default=False)
    data_encrypted = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        path_to_resident_id = "patient__id"

    @property
    def masked_number(self):
        if not self.last_4_digits:
            return ""
        return f"********{self.last_4_digits}"

    def get_account_type_display(self):
        if self.account_type == "1":
            return "Personal Checking"
        elif self.account_type == "2":
            return "Personal Saving"
        elif self.account_type == "3":
            return "Business Checking"
        elif self.account_type == "4":
            return "Business Saving"
        return ""

    @property
    def user_representation(self):
        representation = "Account- "
        if self.account_type:
            account_type_display = self.get_account_type_display()
            representation = f"{account_type_display}- "
        if self.last_4_digits:
            representation = f"{representation}{self.masked_number}"
        return representation

    def __str__(self):
        return self.user_representation


class BillCancellationCodeComposition(GenericModel):
    cancellation_code = LookupField(
        max_length=100, lookup_name="BILL_CANCELLATION_REASON_CODE"
    )
    cancellation_reason = LookupField(
        max_length=100, lookup_name="BILL_CANCELLATION_REASON", unique=True
    )
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("cancellation_code", "cancellation_reason")

    def __str__(self):
        return f"{self.cancellation_code} - {self.cancellation_reason}"


class Bill(GenericModel):
    patient = models.ForeignKey(Resident, on_delete=models.DO_NOTHING)
    practice_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, **optional
    )
    display_id = models.CharField(max_length=512)
    service = models.CharField(max_length=512, **optional)
    service_date = models.DateTimeField()
    statement_date = models.DateTimeField()
    total_charges = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    insurance_paid = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    patient_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    due_date = models.DateTimeField()
    paid_date = models.DateTimeField(**optional)
    status = models.CharField(
        max_length=100,
        choices=TransactionStatus.choices(),
        default=TransactionStatus.PENDING.value,
    )
    cancellation_reason = LookupField(
        max_length=50, lookup_name="BILL_CANCELLATION_REASON", **optional
    )
    cancellation_reason_description = models.TextField(**optional)
    provider = models.ForeignKey(HelixStaff, on_delete=models.SET_NULL, null=True)
    payment_method = models.CharField(
        max_length=100, choices=TransactionMethod.choices(), **optional
    )
    other_discount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    other_adjustment = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    other_writeoff = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    other_tax = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    service_start_date = models.DateTimeField(**optional)
    service_end_date = models.DateTimeField(**optional)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.last_status = self.status

    @property
    def link(self):
        # Lazy import to avoid circular dependency during Django startup
        from customer_backend.managers.tenant import TenantManager

        domain = TenantManager().tenant_obj.domain
        return PAYMENT_LINK_TEMPLATE_URL.format(
            domain=domain, bill_id=str(self.id), uid=str(self.patient.id)
        )

    @property
    def total_refunded_amount(self):
        try:
            all_refunded_requests = BillRefundRequest.objects.filter(
                status__in=SUCCESSFUL_REFUND_REQUEST_STATUSES,
                bill_id=str(self.id),
            )
            return float(
                sum(
                    getattr(refund_request.total_refund_processed, "amount", 0)
                    for refund_request in all_refunded_requests
                )
            )
        except Exception:
            return 0

    @property
    def already_paid_amount_val(self):
        try:
            return float(
                Payment.objects.filter(
                    bill_id=str(self.id),
                    status__in=PAYMENT_ORIGINALLY_DONE_STATUSES,
                    transaction_type=TransactionType.PAYMENT.value,
                ).aggregate(total=Sum("amount"))["total"]
            )
        except Exception:
            return 0

    @property
    def total_refundable_amount(self):
        return float(self.already_paid_amount_val - self.total_refunded_amount)

    @property
    def cancellation_code(self):
        if self.cancellation_reason is None:
            return None

        comp = BillCancellationCodeComposition.objects.filter(
            cancellation_reason=self.cancellation_reason
        ).first()
        if comp is None:
            return None
        return comp.cancellation_code

    def save(self, *args, **kwargs):
        if (
            not self._state.adding
            and self.last_status != self.status
            and self.status == TransactionStatus.COMPLETED.value
        ):
            self.paid_date = datetime.now()
        self.display_id = get_display_id(self)
        return super(Bill, self).save(*args, **kwargs)

    class Meta:
        path_to_location = "encounter__location"
        path_to_resident_id = "patient__id"


class BillRefundRequest(GenericModel):
    display_id = models.CharField(max_length=512, **optional)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    refund_reason = LookupField(
        max_length=100, lookup_name="BILL_REFUND_REASON", **optional
    )
    refund_reason_description = models.TextField(**optional)
    refund_type = models.CharField(
        max_length=100,
        choices=RefundType.choices(),
        default=RefundType.FULL_REFUND.value,
    )
    total_refund_requested = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    total_refund_processed = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    process = models.ForeignKey(to=Process, on_delete=models.DO_NOTHING, **optional)
    status = models.CharField(
        max_length=100,
        choices=RefundRequestStatus.choices(),
        default=RefundRequestStatus.PENDING.value,
    )

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self)
        return super(BillRefundRequest, self).save(*args, **kwargs)


class PaymentDetail(GenericModel):
    saved_card = models.ForeignKey(SavedCard, on_delete=models.DO_NOTHING, **optional)
    saved_account = models.ForeignKey(
        SavedAccount, on_delete=models.SET_NULL, **optional
    )
    payment_method_detail = models.CharField(max_length=255, **optional)
    billing_address_1 = models.CharField(max_length=100, **optional)
    billing_address_2 = models.CharField(max_length=100, **optional)
    billing_city = models.CharField(max_length=100, **optional)
    billing_state = models.CharField(max_length=100, **optional)
    billing_zip = models.CharField(max_length=100, **optional)
    billing_country = models.CharField(max_length=100, **optional)

    class Meta:
        abstract = True


class WriteOff(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    type_of_writeoff = LookupField(max_length=50, lookup_name="DISCOUNT_TYPE")
    value = models.FloatField(default=0, **optional)
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(**optional)
    end_date = models.DateTimeField(**optional)

    def __str__(self):
        return self.name


class Adjustment(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    type_of_adjustment = LookupField(max_length=50, lookup_name="DISCOUNT_TYPE")
    value = models.FloatField()
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(**optional)
    end_date = models.DateTimeField(**optional)

    def __str__(self):
        return self.name


class Payment(PaymentDetail):
    """
    IMPORTANT: Model is more akin to a Transaction which could be either a Payment or a Refund
    """

    display_id = models.CharField(max_length=512, **optional)
    bill = models.ForeignKey(
        Bill, on_delete=models.DO_NOTHING, related_name="payments", **optional
    )
    bill_refund_request = models.ForeignKey(
        BillRefundRequest, on_delete=models.DO_NOTHING, **optional
    )
    transaction_type = models.CharField(
        max_length=100,
        choices=TransactionType.choices(),
        default=TransactionType.PAYMENT.value,
    )
    parent = models.ForeignKey(
        to="self", on_delete=models.CASCADE, db_index=True, **optional
    )
    order_id = models.CharField(max_length=255, **optional)
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    refund_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )
    payment_method = models.CharField(
        max_length=100, choices=TransactionMethod.choices(), **optional
    )
    status = models.CharField(
        max_length=100,
        choices=TransactionStatus.choices(),
        default=TransactionStatus.PENDING.value,
    )
    gateway_status = models.CharField(
        max_length=100, choices=EasyPayTxnStatus.choices(), **optional
    )
    gateway_status_last_updated_on = models.DateTimeField(**optional)
    gateway_recon_last_request_id = models.UUIDField(**optional)
    notes = models.TextField(**optional)
    transaction_id = models.CharField(max_length=255, unique=True, **optional)
    error_message = models.TextField(**optional)
    payment_term = models.IntegerField(default=0, **optional)
    payment_plan = LookupField(
        max_length=50, lookup_name="PAYMENT_PLAN", default="FULL"
    )
    installment_date = models.DateTimeField(**optional)
    write_off = models.ForeignKey(WriteOff, on_delete=models.DO_NOTHING, **optional)
    adjustment = models.ForeignKey(Adjustment, on_delete=models.DO_NOTHING, **optional)
    write_off_amount_overridden = models.BooleanField(**optional)
    adjustment_amount_overridden = models.BooleanField(**optional)
    extra_data = models.JSONField(**optional)

    class Meta:
        path_to_location = "bill__encounter__location"
        path_to_resident_id = "bill__patient__id"
        verbose_name = "transaction"

    @property
    def method(self):
        return self.payment_method

    def get_card_info_from_extra_data(self):
        if not self.extra_data:
            return None

        card_type = self.extra_data.get("WidgetArgs", {}).get("cardType")
        mask = self.extra_data.get("WidgetArgs", {}).get("Mask")

        if card_type and mask:
            return f"{card_type}- {mask}"

        return None

    def get_card_info_from_notes(self):
        try:
            notes_dict = json.loads(self.notes)
            card_type = notes_dict.get("WidgetArgs", {}).get("cardType")
            mask = notes_dict.get("WidgetArgs", {}).get("Mask")

            if card_type and mask:
                return f"{card_type}- {mask}"

            return None
        except Exception:
            return None

    @property
    def card_info(self):
        if (self.transaction_type == TransactionType.REFUND.value) or (
            self.method not in CARD_BASED_TRANSACTION_METHODS
        ):
            return None

        if self.method == TransactionMethod.POS_PAYMENT.value:
            card_info = self.get_card_info_from_extra_data()
            if not card_info:
                return self.get_card_info_from_notes()

        try:
            return self.saved_card.user_representation
        except Exception:
            return "Card"

    @property
    def account_info(self):
        if (self.transaction_type == TransactionType.REFUND.value) or (
            self.method != TransactionMethod.BANK_TRANSFER.value
        ):
            return

        try:
            return self.saved_account.user_representation
        except Exception:
            return "Account"

    @property
    def refundable_amount(self):
        if self.transaction_type == TransactionType.REFUND.value:
            return 0
        try:
            isolated_refundable_amount = float(
                self.amount.amount - self.refund_amount.amount
            )
            bill_refundable_amount = self.bill.total_refundable_amount
            return min(isolated_refundable_amount, bill_refundable_amount)
        except Exception:
            return 0

    def save(self, *args, **kwargs):
        if (
            self._state.adding
            and self.transaction_type == TransactionType.PAYMENT.value
            and self.payment_method is None
        ):
            self.payment_method = TransactionMethod.CREDIT_CARD.value

        if self._state.adding:
            self.display_id = get_display_id(self)
            if (
                self.bill is None
                and self.transaction_type == TransactionType.REFUND.value
            ):
                self.bill_id = self.bill_refund_request.bill_id
        return super(Payment, self).save(*args, **kwargs)

    def log(
        self, event, data, call_log=None, source=TransactionEventSource.SYSTEM.value
    ):
        from payments.managers.transaction.log import TransactionLogManager

        log_manager = TransactionLogManager(transaction_obj=self)
        return log_manager.log(event=event, source=source, data=data, call_log=call_log)


class BillSummary(GenericModel):
    bill = models.ForeignKey(Bill, on_delete=models.DO_NOTHING, related_name="summary")
    title = models.CharField(max_length=255, **optional)
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )

    class Meta:
        path_to_location = "bill__encounter__location"
        path_to_resident_id = "bill__patient__id"


class BillBreakDown(GenericModel):
    CATEGORY = [
        ("CONSULTATION", "Consultation"),
        ("MEDICATIONS", "Medications"),
        ("LAB", "Lab Work"),
    ]
    bill = models.ForeignKey(
        Bill, on_delete=models.DO_NOTHING, related_name="breakdown"
    )
    date = models.DateTimeField()
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, **optional)
    type_of_service = models.ForeignKey(
        TypeOfService, on_delete=models.DO_NOTHING, **optional
    )
    # below fields are added for safety purposes, like if service amount changed in future, it should not effect the older bills
    category_name = models.CharField(max_length=255, **optional)
    type_of_service_name = models.CharField(max_length=255, **optional)
    type_of_service_amount = MoneyField(
        max_digits=14, default=0, decimal_places=2, default_currency="USD"
    )
    description = models.CharField(max_length=512, **optional)
    quantity = models.FloatField(**optional)
    other_fees = MoneyField(
        max_digits=14, default=0, decimal_places=2, default_currency="USD"
    )
    other_fees_taxable = models.BooleanField(default=True)
    insurance_amount = MoneyField(
        max_digits=14, decimal_places=2, default=0, default_currency="USD"
    )
    patient_amount = MoneyField(
        max_digits=14, default=0, decimal_places=2, default_currency="USD"
    )
    tax = MoneyField(max_digits=14, decimal_places=2, default=0, default_currency="USD")
    total_amount = MoneyField(
        max_digits=14, default=0, decimal_places=2, default_currency="USD"
    )
    sub_total = MoneyField(
        max_digits=14, default=0, decimal_places=2, default_currency="USD", **optional
    )
    service_start_date = models.DateTimeField(**optional)
    service_end_date = models.DateTimeField(**optional)

    class Meta:
        path_to_location = "bill__encounter__location"
        path_to_resident_id = "bill__patient__id"


class AbstractDiscountUsage(GenericModel):
    discount = models.ForeignKey(Discount, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    type_of_discount = LookupField(max_length=50, lookup_name="DISCOUNT_TYPE")
    value = models.FloatField()
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", default=0
    )
    taxable = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AbstractAdjustmentUsage(GenericModel):
    adjustment = LookupField(max_length=50, lookup_name="BILL_ADJUSTMENT", **optional)
    adjustment_type = LookupField(
        max_length=50, lookup_name="BILL_ADJUSTMENT_TYPE", **optional
    )
    adj_obj = models.ForeignKey(Adjustment, on_delete=models.SET_NULL, **optional)
    name = models.CharField(max_length=255, **optional)
    type_of_adjustment = LookupField(
        max_length=50, lookup_name="DISCOUNT_TYPE", **optional
    )
    value = models.FloatField(**optional)
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    taxable = models.BooleanField(default=True)

    class Meta:
        abstract = True


class AbstractWriteoffUsage(GenericModel):
    write_off = LookupField(max_length=50, lookup_name="BILL_WRITE_OFF", **optional)
    write_off_obj = models.ForeignKey(WriteOff, on_delete=models.SET_NULL, **optional)
    name = models.CharField(max_length=255, **optional)
    type_of_writeoff = LookupField(
        max_length=50, lookup_name="DISCOUNT_TYPE", **optional
    )
    value = models.FloatField(**optional)
    max_upto = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency="USD")
    taxable = models.BooleanField(default=True)

    class Meta:
        abstract = True


class TransactionWriteOff(AbstractWriteoffUsage):
    transaction = models.ForeignKey(Payment, on_delete=models.DO_NOTHING)


class TransactionAdjustment(AbstractAdjustmentUsage):
    transaction = models.ForeignKey(Payment, on_delete=models.DO_NOTHING)


class BreakdownDiscount(AbstractDiscountUsage):
    breakdown = models.ForeignKey(
        BillBreakDown, on_delete=models.CASCADE, related_name="discounts"
    )


class BreakdownAdjustment(AbstractAdjustmentUsage):
    breakdown = models.ForeignKey(
        BillBreakDown, on_delete=models.CASCADE, related_name="adjustments"
    )


class BreakdownWriteoff(AbstractWriteoffUsage):
    breakdown = models.ForeignKey(
        BillBreakDown, on_delete=models.CASCADE, related_name="writeoffs"
    )


class BillDiscount(AbstractDiscountUsage):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="discounts")


class BillAdjustment(AbstractAdjustmentUsage):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="adjustments")


class BillWriteoff(AbstractWriteoffUsage):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="writeoffs")


class PaymentPlan(GenericModel):
    name = models.CharField(max_length=255, unique=True)
    duration = models.IntegerField()
    interest_rate = models.FloatField(default=0, **optional)
    other_fees = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    interest_taxable = models.BooleanField(default=True)
    other_fees_taxable = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    type_of_interest = LookupField(max_length=50, lookup_name="PAYMENT_PLAN_TYPE")
    type_processing_fee = LookupField(max_length=50, lookup_name="PAYMENT_PLAN_TYPE")
    start_date = models.DateTimeField(**optional)
    end_date = models.DateTimeField(**optional)
    terms_condition = models.ForeignKey(
        Policy, on_delete=models.DO_NOTHING, related_name="terms_condition", **optional
    )
    privacy_policy = models.ForeignKey(
        Policy, on_delete=models.DO_NOTHING, related_name="privacy_policy", **optional
    )
    description = models.TextField(**optional)

    def __str__(self):
        return self.name


class BillPaymentPlan(PaymentDetail):
    bill = models.OneToOneField(Bill, on_delete=models.CASCADE, related_name="pp")
    payment_plan = models.ForeignKey(PaymentPlan, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=255, **optional)
    duration = models.IntegerField(**optional)
    fees = MoneyField(
        max_digits=14, decimal_places=2, default_currency="USD", **optional
    )
    interest_rate = models.FloatField(default=0, **optional)
    interest_amount = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
    )
    tax = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
    )
    payable_amount_using_pp = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
    )
    status = LookupField(max_length=50, lookup_name="BILL_PLAN_STATUS")
    emi = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="USD",
    )
    start_date = models.DateTimeField()
    day_of_month = models.IntegerField()
    consent_id = models.CharField(
        max_length=255,
    )
    payment_method = LookupField(
        max_length=50, lookup_name="PAYMENT_METHODS", default="CREDIT_CARD"
    )
    consent_response = models.JSONField(**optional)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.name = self.payment_plan.name
            self.duration = self.payment_plan.duration
            self.fees = self.payment_plan.other_fees
            self.interest_rate = self.payment_plan.interest_rate
        return super().save(*args, **kwargs)

    class Meta:
        path_to_location = "bill__encounter__location"
        path_to_resident_id = "bill__patient__id"
