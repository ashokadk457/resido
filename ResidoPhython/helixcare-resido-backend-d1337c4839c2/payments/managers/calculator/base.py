from .discounts import DiscountCalculator
from .adjustment import AdjustmentCalculator
from .writeoff import WriteoffCalculator
from .tax import TaxCalculator


class BaseCalculator:
    @staticmethod
    def _get_adjustments_total(adjustments, total_amount):
        total, taxable = 0, 0
        for obj in adjustments:
            manager = AdjustmentCalculator(
                adj_obj=obj.get("adj_obj"),
                amount=total_amount,
                adjustment_type=obj.get("adjustment_type"),
            )
            value = manager.calculate_adjustment()
            total += value
            if value < 0:
                if not obj.get("taxable"):
                    taxable += value
            else:
                if obj.get("taxable"):
                    taxable += value
        return round(float(total), 2), round(float(taxable), 2)

    @staticmethod
    def _get_discounts_total(discounts, total_amount):
        total, taxable = 0, 0
        for obj in discounts:
            manager = DiscountCalculator(
                discount_obj=obj.get("discount"),
                amount=total_amount,
            )
            value = manager.calculate_discount()
            total += value
            if not obj.get("taxable"):
                taxable += float(value)
        return round(float(total), 2), round(float(taxable), 2)

    @staticmethod
    def _get_writeoffs_total(writeoffs, total_amount):
        total, taxable = 0, 0
        for obj in writeoffs:
            manager = WriteoffCalculator(
                writeoff_obj=obj.get("write_off_obj"), amount=total_amount
            )
            value = manager.calculate_writeoff()
            total += value
            if not obj.get("taxable"):
                taxable += value
        return round(float(total), 2), round(float(taxable), 2)

    @staticmethod
    def calculate_tax(amount, state, place_of_tax):
        mngr = TaxCalculator(state=state, amount=amount, place_of_tax=place_of_tax)
        return mngr.calculate()
