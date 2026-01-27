class BasePaymentGateway:
    def __init__(self, **kwargs):
        self.config = kwargs.get("config")
        self.bill = kwargs.get("bill")
        self.bill_id = (
            str(self.bill.id) if self.bill is not None else kwargs.get("bill_id")
        )
        self.transaction_obj = kwargs.get("transaction_obj")
        self.transaction_id = (
            str(self.transaction_obj.id)
            if self.transaction_obj is not None
            else kwargs.get("transaction_id")
        )

    def process_payment_card(
        self, amount, card, cvv, payment_term, installment_date
    ) -> dict:
        raise NotImplementedError()

    def process_payment_account(self, amount, account) -> dict:
        raise NotImplementedError()

    def prepare_request_for_pos_payment(self, payment_obj, amount):
        raise NotImplementedError()
