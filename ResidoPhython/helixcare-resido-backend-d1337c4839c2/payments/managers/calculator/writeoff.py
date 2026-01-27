class WriteoffCalculator:
    def __init__(self, writeoff_obj, amount):
        self.writeoff_obj = writeoff_obj
        self.amount = float(amount)

    def calculate_writeoff(self):
        if self.writeoff_obj.type_of_writeoff == "PERCENT":
            return self._calculate_percent_writeoff()
        else:
            return self._calculate_flat_writeoff()

    def _calculate_percent_writeoff(self):
        percentage = self.writeoff_obj.value
        percent_amount = round(self.amount * percentage / 100, 2)
        if (
            self.writeoff_obj.max_upto
            and percent_amount > self.writeoff_obj.max_upto.amount
        ):
            percent_amount = float(self.writeoff_obj.max_upto.amount)
        return percent_amount

    def _calculate_flat_writeoff(self):
        discount_amount = float(self.writeoff_obj.value)
        if discount_amount > self.amount:
            return self.amount
        return discount_amount
