from .base import BaseCalculator
from payments.constants import PlaceOfTax


class BreakdownCalculator(BaseCalculator):
    def append_totals_to_data(self, data, adjustments, discounts, writeoffs):
        sub_total = round(
            float(data.get("type_of_service").amount.amount) * data.get("quantity"), 2
        )
        insurance_amount = (
            float(data.get("insurance_amount").amount)
            if data.get("insurance_amount")
            else 0
        )
        total = sub_total - insurance_amount
        taxable_amount = sub_total - insurance_amount
        total += float(data.get("other_fees").amount)
        taxable_amount += (
            float(data.get("other_fees").amount)
            if data.get("other_fees_taxable", False)
            else 0
        )
        self.adj_applied, self.disc_applied, self.wrt_applied = False, False, False
        if total > 0:
            adj_amount, adj_tax_amount = self._get_adjustments_total(
                adjustments=adjustments, total_amount=sub_total
            )
            total += adj_amount
            taxable_amount += adj_tax_amount
            self.adj_applied = True
        if total > 0:
            disc_amount, disc_tax_amount = self._get_discounts_total(
                discounts=discounts, total_amount=sub_total
            )  # TODO: Adjust discount calculations according to other discounts calculated rather than subtotal
            total -= disc_amount
            taxable_amount -= disc_tax_amount
            self.disc_applied = True
        if total > 0:
            wrt_amount, wrt_tax_amount = self._get_writeoffs_total(
                writeoffs=writeoffs, total_amount=sub_total
            )
            total -= wrt_amount
            taxable_amount -= wrt_tax_amount
            self.wrt_applied = True
        if total < 0:
            total = 0
            taxable_amount = 0
        data["total_amount"] = round(total, 2)
        data["total_amount_currency"] = data.get("type_of_service").amount_currency
        state = (
            data.get("bill").practice_location.state
            if data.get("bill") and data.get("bill").practice_location
            else data.get("tax_state", None)
        )
        state = state.upper() if state else None
        data["tax"] = round(
            (
                self.calculate_tax(
                    amount=taxable_amount, state=state, place_of_tax=PlaceOfTax.PRIMARY
                )
                if data.get("type_of_service").taxable and taxable_amount > 0
                else 0
            ),
            2,
        )
        data["tax_currency"] = data["total_amount_currency"]
        data["patient_amount"] = data["total_amount"] + data["tax"]
        data["patient_amount_currency"] = data.get("type_of_service").amount_currency
        return data
