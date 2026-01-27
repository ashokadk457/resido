from payments.models import TaxPerState
from payments.constants import PlaceOfTax


class TaxCalculator:
    def __init__(self, state, amount, place_of_tax):
        self.tax_obj = self._get_tax_rate_as_per_state(state=state)
        self.amount = amount
        self.place_of_tax = place_of_tax

    @staticmethod
    def _get_tax_rate_as_per_state(state):
        query = TaxPerState.objects.filter(state__iexact=state).first()
        if not query:
            # by default fallback to 5% tax
            return TaxPerState(tax_type="PERCENT", value=5, max_upto=None)
        return query

    def calculate(self):
        if self.tax_obj.tax_type == "FLAT":
            return self._calculate_flat_tax()
        return self._calculate_percent_tax()

    def _calculate_flat_tax(self):
        if self.place_of_tax is PlaceOfTax.SECONDARY:
            return 0
        return self.tax_obj.value

    def _calculate_percent_tax(self):
        percent = self.tax_obj.value
        percent_amount = round(self.amount * percent / 100, 2)
        if (
            self.tax_obj.max_upto
            and self.tax_obj.max_upto.amount > 0
            and percent_amount > float(self.tax_obj.max_upto.amount)
        ):
            return float(self.tax_obj.max_upto.amount)
        return percent_amount
