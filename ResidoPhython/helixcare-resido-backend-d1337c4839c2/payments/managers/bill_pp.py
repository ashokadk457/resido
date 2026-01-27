import time
from datetime import datetime
from djmoney.money import Money
from django.db.models import Sum

from common.utils.logging import logger
from payments.constants import PlaceOfTax
from payments.models import BillPaymentPlan, Payment
from payments.serializers import BillPaymentPlanSerializer
from payments.managers.calculator.tax import TaxCalculator
from payments.helix_payment_processor import HelixPaymentProcessor


class BillPaymentPlanManager:
    def __init__(
        self,
        bill,
        payment_plan,
        payment_method,
        pp_start_date,
        card=None,
        cvv=None,
        account=None,
        save_method=False,
    ):
        self.bill = bill
        self.payment_plan = payment_plan
        self.consent_days = self.payment_plan.duration * 31
        self.payment_method = payment_method
        self.card = card
        self.cvv = cvv
        self.pp_start_date = pp_start_date
        self.account = account
        patient = bill.patient
        self.bill_plan = BillPaymentPlan(
            bill=bill,
            payment_plan=payment_plan,
            start_date=pp_start_date,
            day_of_month=pp_start_date.day,
            payment_method=self.payment_method,
            saved_card=card if save_method else None,
            saved_account=account if save_method else None,
            billing_address_1=(
                card.billing_address_1
                if card and card.billing_address_1
                else (
                    account.billing_address_1
                    if account and account.billing_address_1
                    else patient.address
                )
            ),
            billing_address_2=(
                card.billing_address_2
                if card and card.billing_address_2
                else (
                    account.billing_address_2
                    if account and account.billing_address_2
                    else patient.address_1
                )
            ),
            billing_city=(
                card.billing_city
                if card and card.billing_city
                else (
                    account.billing_city
                    if account and account.billing_city
                    else patient.city
                )
            ),
            billing_state=(
                card.billing_state
                if card and card.billing_state
                else (
                    account.billing_state
                    if account and account.billing_state
                    else patient.state
                )
            ),
            billing_zip=(
                card.billing_zip
                if card and card.billing_zip
                else (
                    account.billing_zip
                    if account and account.billing_zip
                    else patient.zipcode
                )
            ),
            billing_country=(
                card.billing_country
                if card and card.billing_country
                else (
                    account.billing_country
                    if account and account.billing_country
                    else patient.country
                )
            ),
            payment_method_detail=(
                card.last_4_digits
                if card
                else (
                    account.account_number[-4:]
                    if account and account.account_number
                    else None
                )
            ),
        )
        self.calculate_charges_and_emi()
        self.gateway = HelixPaymentProcessor.get_payment_gateway(
            currency=str(self.bill.patient_amount.currency),
            bill=self.bill,
        )

    def process_consent(self):
        if self.payment_method in ["CREDIT_CARD", "DEBIT_CARD"]:
            resp = self._process_card_consent()
        elif self.payment_method == "BANK_TRANSFER":
            resp = self._process_account_consent()
        else:
            return None
        if not resp.get("success"):
            return False, None, resp.get("error_code"), resp.get("error")
        self.bill_plan.consent_id = resp.get("data").get("ConsentID")
        self.bill_plan.consent_response = resp.get("data")
        self.bill_plan.save()
        self.bill.status = "ON_PP"
        self.bill.save()
        data = BillPaymentPlanSerializer(self.bill_plan).data
        return True, data, None, None

    def _process_card_consent(self):
        return self.gateway.create_consent_on_card(
            full_amount=self.payable_amount_using_pp,
            emi_amount=self.emi,
            start_date=self.pp_start_date,
            consent_days=self.consent_days,
            card=self.card,
            cvv=self.cvv,
        )

    def _process_account_consent(self):
        return self.gateway.create_consent_on_account(account=self.account)

    @staticmethod
    def _calculate_charges_and_emi(
        amount,
        interest_rate,
        interest_rate_taxable,
        fees,
        fees_taxable,
        duration,
        type_of_interest,
        type_processing_fee,
        state=None,
    ):
        interest_amount = (
            round(amount * interest_rate / 100, 2)
            if type_of_interest == "PERCENT"
            else interest_rate
        )
        interest_amount_tax = round(
            (
                TaxCalculator(
                    state=state,
                    amount=interest_amount,
                    place_of_tax=PlaceOfTax.SECONDARY,
                ).calculate()
                if interest_rate_taxable
                else 0
            ),
            2,
        )
        fees_amount = (
            round(amount * fees / 100, 2) if type_processing_fee == "PERCENT" else fees
        )
        fees_tax = round(
            (
                TaxCalculator(
                    state=state, amount=fees_amount, place_of_tax=PlaceOfTax.SECONDARY
                ).calculate()
                if fees_taxable
                else 0
            ),
            2,
        )
        amount += interest_amount + interest_amount_tax + fees_tax + fees_amount
        emi = round(amount / duration, 2)
        return amount, emi, interest_amount, interest_amount_tax, fees_amount, fees_tax

    def calculate_charges_and_emi(self):
        pat_amount = float(self.bill.patient_amount.amount)
        (
            self.payable_amount_using_pp,
            self.emi,
            self.pp_interest_amount,
            self.pp_interest_amount_tax,
            self.pp_fees,
            self.pp_fees_tax,
        ) = self._calculate_charges_and_emi(
            amount=pat_amount,
            interest_rate=self.payment_plan.interest_rate or 0,
            interest_rate_taxable=self.payment_plan.interest_taxable or False,
            fees=(
                float(self.payment_plan.other_fees.amount)
                if self.payment_plan.other_fees
                else 0
            ),
            fees_taxable=self.payment_plan.other_fees_taxable or False,
            duration=self.payment_plan.duration,
            state=(
                self.bill.practice_location.state
                if self.bill.practice_location
                else None
            ),
            type_of_interest=self.payment_plan.type_of_interest,
            type_processing_fee=self.payment_plan.type_processing_fee,
        )
        total_tax = self.pp_fees_tax + self.pp_interest_amount_tax
        self.pp_total = round(
            self.pp_fees
            + self.pp_interest_amount
            + self.pp_fees_tax
            + self.pp_interest_amount_tax,
            2,
        )
        self.bill_plan.interest_amount = Money(
            amount=self.pp_interest_amount, currency=self.bill.patient_amount.currency
        )
        self.bill_plan.tax = Money(
            amount=total_tax, currency=self.bill.patient_amount.currency
        )
        self.bill_plan.payable_amount_using_pp = Money(
            amount=self.payable_amount_using_pp,
            currency=self.bill.patient_amount.currency,
        )
        self.bill_plan.emi = Money(
            amount=self.emi, currency=self.bill.patient_amount.currency
        )
        return self.pp_total

    @staticmethod
    def get_all_bills_due_for_today():
        todays_date = datetime.now()
        todays_day = todays_date.day
        bill_pps = BillPaymentPlan.objects.filter(
            day_of_month=todays_day, status="ACTIVE"
        )
        bill_ids = [obj.bill_id for obj in bill_pps]
        already_billed_bills = {
            o: True
            for o in Payment.objects.filter(
                created_on__date=todays_date, bill__in=bill_ids, status="COMPLETED"
            ).values_list("bill", flat=True)
        }
        return [obj for obj in bill_pps if not already_billed_bills.get(obj.bill_id)]

    @classmethod
    def charge_payment_for_bill_pp(cls, bill_pp):
        bill = bill_pp.bill
        payment = Payment.objects.create(
            order_id=f"PAY-{int(time.time())}",
            amount=bill_pp.emi,
            bill=bill,
            payment_method=bill_pp.payment_method,
            status="PENDING",
        )
        gateway = HelixPaymentProcessor.get_payment_gateway(
            currency=bill.patient_amount.currency, bill=bill, payment_obj=payment
        )
        if bill_pp.payment_method in ["CREDIT_CARD", "DEBIT_CARD"]:
            resp = gateway.charge_cc_using_consent(
                consent_id=bill_pp.consent_id, amount=bill_pp.emi
            )
        else:
            resp = gateway.charge_acc_using_consent(
                consent_id=bill_pp.consent_id, amount=bill_pp.emi
            )
        status = "COMPLETED" if resp.get("success") else "FAILED"
        payment.status = status
        payment.notes = resp.get("data")
        payment.transaction_id = (
            resp.get("data").get("TxID") if resp.get("success") else None
        )
        payment.save()
        if status == "COMPLETED":
            cls.check_and_update_bill_and_plan_status(bill=bill, bill_pp=bill_pp)

    @staticmethod
    def check_and_update_bill_and_plan_status(bill, bill_pp):
        already_paid_amount = float(
            Payment.objects.filter(bill=bill, status="COMPLETED").aggregate(
                total=Sum("amount")
            )["total"]
        )
        to_be_paid_amount = float(bill_pp.payable_amount_using_pp.amount)
        if already_paid_amount == to_be_paid_amount:
            bill.status = "COMPLETED"
            bill.payment_method = bill_pp.payment_method
            bill.save()
            bill_pp.status = "CLOSED"
            bill_pp.save()

    @classmethod
    def process_bill_plan_payments(cls):
        all_bill_pps = cls.get_all_bills_due_for_today()
        total = len(all_bill_pps)
        success, failed = 0, 0
        for bill_pp in all_bill_pps:
            try:
                cls.charge_payment_for_bill_pp(bill_pp=bill_pp)
                success += 1
            except Exception as e:
                logger.info(
                    f"Exception while calling charge_payment_for_bill_pp for bill_pp ({bill_pp.id}), Error: {e}"
                )
                failed += 1
        return total, success, failed
