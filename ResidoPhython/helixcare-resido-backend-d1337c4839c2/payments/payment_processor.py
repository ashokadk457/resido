from payments.models import SavedCard, SavedAccount
from payments.gateway.base import BasePaymentGateway


class PaymentProcessor:
    def __init__(self, gateway: BasePaymentGateway):
        self.gateway = gateway

    def set_gateway(self, gateway: BasePaymentGateway):
        self.gateway = gateway

    def make_payment_card(
        self,
        amount: float,
        card: SavedCard,
        cvv: str,
        payment_term: int,
        installment_date,
    ) -> dict:
        return self.gateway.process_payment_card(
            amount, card, cvv, payment_term, installment_date
        )

    def make_payment_account(self, amount: float, card: SavedAccount) -> dict:
        return self.gateway.process_payment_account(amount, card)

    def prepare_for_pos_payment(self, payment_obj, amount: float):
        return self.gateway.prepare_request_for_pos_payment(
            payment_obj=payment_obj, amount=amount
        )
