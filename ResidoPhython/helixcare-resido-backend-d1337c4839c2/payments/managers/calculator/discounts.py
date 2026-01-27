class DiscountCalculator:
    def __init__(self, discount_obj, amount):
        self.discount_obj = discount_obj
        self.amount = float(amount)

    def calculate_discount(self):
        if self.discount_obj.type_of_discount == "PERCENT":
            return self._calculate_percent_discount()
        else:
            return self._calculate_flat_discount()

    def _calculate_percent_discount(self):
        percentage = self.discount_obj.value
        percent_amount = round(self.amount * percentage / 100, 2)
        if (
            self.discount_obj.max_upto
            and percent_amount > self.discount_obj.max_upto.amount
        ):
            percent_amount = float(self.discount_obj.max_upto.amount)
        return percent_amount

    def _calculate_flat_discount(self):
        discount_amount = float(self.discount_obj.value)
        if discount_amount > self.amount:
            return self.amount
        return discount_amount
