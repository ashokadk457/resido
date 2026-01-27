import re
from rest_framework.exceptions import APIException
from payments.models import Bill
from payments.payment_constants import TransactionMethod, TransactionStatus
from payments.payment_processor import PaymentProcessor
from payments.gateway.easypay.core import EasyPay


class HelixPaymentProcessor:
    @staticmethod
    def process_payment(
        payment, cvv, payment_term, installment_date, card=None, account=None
    ):
        amount = payment.amount
        gateway = HelixPaymentProcessor.get_payment_gateway(
            currency=payment.amount_currency, bill=payment.bill, payment_obj=payment
        )

        if not gateway:
            raise APIException("Unsupported currency")

        processor = PaymentProcessor(gateway)
        confirmation = None

        patient = payment.bill.patient
        payment.billing_address_1 = (
            card.billing_address_1
            if card and card.billing_address_1
            else (
                account.billing_address_1
                if account and account.billing_address_1
                else patient.address
            )
        )
        payment.billing_address_2 = (
            card.billing_address_2
            if card and card.billing_address_2
            else (
                account.billing_address_2
                if account and account.billing_address_2
                else patient.address_1
            )
        )
        payment.billing_city = (
            card.billing_city
            if card and card.billing_city
            else (
                account.billing_city
                if account and account.billing_city
                else patient.city
            )
        )
        payment.billing_state = (
            card.billing_state
            if card and card.billing_state
            else (
                account.billing_state
                if account and account.billing_state
                else patient.state
            )
        )
        payment.billing_zip = (
            card.billing_zip
            if card and card.billing_zip
            else (
                account.billing_zip
                if account and account.billing_zip
                else patient.zipcode
            )
        )
        payment.billing_country = (
            card.billing_country
            if card and card.billing_country
            else (
                account.billing_country
                if account and account.billing_country
                else patient.country
            )
        )
        payment.payment_method_detail = (
            card.last_4_digits
            if card
            else (
                account.account_number[-4:]
                if account and account.account_number
                else None
            )
        )

        if payment.payment_method in [
            TransactionMethod.CREDIT_CARD.value,
            TransactionMethod.DEBIT_CARD.value,
        ]:
            confirmation = processor.make_payment_card(
                amount, card, cvv, payment_term, installment_date
            )

        elif payment.payment_method == TransactionMethod.BANK_TRANSFER.value:
            confirmation = processor.make_payment_account(amount, account)

        elif payment.payment_method == TransactionMethod.POS_PAYMENT.value:
            confirmation = processor.prepare_for_pos_payment(
                payment_obj=payment, amount=amount.amount
            )

        elif payment.payment_method == TransactionMethod.CASH.value:
            confirmation = {
                "success": True,
                "data": {
                    "message": "Cash received",
                    "amount": float(amount.amount),
                },
            }

        payment_process_data = {"message": "Payment processed successfully."}
        if (
            confirmation.get("success")
            or confirmation.get("message") == "POS Payment request prepared"
        ):
            if confirmation.get("success"):
                HelixPaymentProcessor.update_transaction_post_processing(
                    payment=payment,
                    status=TransactionStatus.COMPLETED.value,
                    notes=confirmation.get("data"),
                    extra_data=confirmation.get("data", {}),
                    transaction_id=confirmation.get("transaction_id"),
                )
            if confirmation.get("message") == "POS Payment request prepared":
                payment_process_data = confirmation
            return payment_process_data
        else:
            error_message = confirmation.get("error", "Unknown error")
            HelixPaymentProcessor.update_transaction_post_processing(
                payment=payment,
                status=TransactionStatus.FAILED.value,
                notes=error_message,
                extra_data=confirmation.get("data", {}),
                transaction_id=confirmation.get("transaction_id"),
            )
            raise APIException(f"Error occurred in payment processing: {error_message}")

    @staticmethod
    def get_payment_gateway(currency: str, bill, payment_obj=None):
        if currency == "USD":
            return EasyPay(bill=bill, transaction_obj=payment_obj)
        return None

    @staticmethod
    def get_transaction_id(notes):
        if isinstance(notes, dict):
            try:
                return notes["CreditCardSale_ManualResult"]["TxID"]
            except (KeyError, TypeError):
                pass
        if not isinstance(notes, str):
            return None
        match = re.search(r"[\"']TxID[\"']:\s*(\d+)", notes or "")
        return match.group(1) if match else None

    @staticmethod
    def update_transaction_post_processing(
        payment, status, notes, extra_data=None, transaction_id=None
    ):
        # TODO EVENTUALLY MOVE TO PAYMENT MANAGER
        transaction_id = (
            transaction_id
            if transaction_id is not None
            else HelixPaymentProcessor.get_transaction_id(notes=notes)
        )
        payment.extra_data = extra_data
        payment.status = status
        payment.notes = notes
        payment.transaction_id = (
            str(transaction_id) if transaction_id is not None else None
        )
        payment.save()

        bill = payment.bill
        if status == TransactionStatus.COMPLETED.value:
            already_paid_amount = bill.already_paid_amount_val
            to_be_paid_amount = float(payment.bill.patient_amount.amount)
            if already_paid_amount is not None:
                bill = Bill.objects.get(id=payment.bill.id)
                bill_status = TransactionStatus.PARTIALLY_COMPLETED.value
                if already_paid_amount == to_be_paid_amount:
                    bill_status = TransactionStatus.COMPLETED.value
                bill.payment_method = payment.payment_method
                bill.status = bill_status
                bill.save()

        return payment
