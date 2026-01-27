class AdjustmentCalculator:
    def __init__(self, adj_obj, amount, adjustment_type="POS"):
        self.adj_obj = adj_obj
        self.amount = float(amount)
        self.adjustment_type = adjustment_type

    def calculate_adjustment(self):
        if self.adj_obj.type_of_adjustment == "PERCENT":
            amount = self._calculate_percent_adjustment()
        else:
            amount = self._calculate_flat_adjustment()
        return amount if self.adjustment_type == "POS" else -amount

    def _calculate_percent_adjustment(self):
        percentage = self.adj_obj.value
        percent_amount = round(self.amount * percentage / 100, 2)
        if self.adj_obj.max_upto and percent_amount > self.adj_obj.max_upto.amount:
            percent_amount = float(self.adj_obj.max_upto.amount)
        return percent_amount

    def _calculate_flat_adjustment(self):
        discount_amount = float(self.adj_obj.value)
        if discount_amount > self.amount:
            return self.amount
        return discount_amount
