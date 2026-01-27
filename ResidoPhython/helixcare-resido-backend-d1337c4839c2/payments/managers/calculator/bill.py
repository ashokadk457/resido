from .base import BaseCalculator
from payments.constants import PlaceOfTax


class BillCalculator(BaseCalculator):
    def append_totals_to_data(
        self, data, breakdowns, adjustments=[], discounts=[], writeoffs=[]
    ):
        data["total_charges"] = 0
        data["patient_amount"] = 0
        data["insurance_paid"] = 0
        for obj in breakdowns:
            data["total_charges"] += obj.get("total_amount")
            data["total_charges_currency"] = obj.get("total_amount_currency")
            data["patient_amount"] += obj.get("patient_amount")
            data["patient_amount_currency"] = obj.get("patient_amount_currency")
            data["insurance_paid"] += (
                float(obj.get("insurance_amount").amount)
                if obj.get("insurance_amount")
                else 0
            )
            data["insurance_paid_currency"] = (
                obj.get("insurance_amount").currency
                if obj.get("insurance_amount")
                else "USD"
            )
        sub_total_taxable = 0
        sub_total = data["patient_amount"]
        data["other_adjustment"], data["other_discount"], data["other_writeoff"] = (
            0,
            0,
            0,
        )
        data["other_writeoff_currency"] = data["total_charges_currency"]
        data["other_adjustment_currency"] = data["total_charges_currency"]
        data["other_discount_currency"] = data["total_charges_currency"]
        data["other_tax_currency"] = data["total_charges_currency"]
        adj_amount, adj_tax_amount = self._get_adjustments_total(
            adjustments=adjustments, total_amount=data["total_charges"]
        )
        disc_amount, disc_tax_amount = self._get_discounts_total(
            discounts=discounts, total_amount=data["total_charges"]
        )
        wrt_amount, wrt_tax_amount = self._get_writeoffs_total(
            writeoffs=writeoffs, total_amount=data["total_charges"]
        )
        self.adj_applied, self.disc_applied, self.wrt_applied = False, False, False
        if sub_total > 0 and adj_amount > 0:
            sub_total += adj_amount
            data["other_adjustment"] = adj_amount
            self.adj_applied = True
            sub_total_taxable += adj_tax_amount
        if sub_total > 0 and disc_amount > 0:
            sub_total -= disc_amount
            data["other_discount"] = disc_amount
            self.disc_applied = True
            sub_total_taxable -= disc_tax_amount
        if sub_total > 0 and wrt_amount > 0:
            sub_total -= wrt_amount
            data["other_writeoff"] = wrt_amount
            sub_total_taxable -= wrt_tax_amount
            self.wrt_applied = True
        if sub_total < 0:
            sub_total = 0
            sub_total_taxable = 0
        state = (
            data.get("practice_location").state
            if data.get("practice_location")
            else None
        )
        tax_on_sub_total = self.calculate_tax(
            amount=sub_total_taxable, state=state, place_of_tax=PlaceOfTax.SECONDARY
        )
        data["patient_amount"] = sub_total + tax_on_sub_total
        data["other_tax"] = tax_on_sub_total
        data["other_tax_currency"] = data["total_charges_currency"]
        return data

    @classmethod
    def _calculate_static_summary(cls, instance, breakdowns):
        tax, adjustment, discount, writeoff, insurance, other_fees = (
            float(instance.other_tax.amount),
            float(instance.other_adjustment.amount),
            float(instance.other_discount.amount),
            float(instance.other_writeoff.amount),
            0,
            0,
        )
        (
            tax_currency,
            adjustment_currency,
            discount_currency,
            insurance_currency,
            writeoff_currency,
            other_fees_currency,
        ) = (0, 0, 0, 0, 0, 0)
        for obj in breakdowns:
            all_adjustments = obj.adjustments.all()
            adj_amount, _ = cls._get_adjustments_total(
                adjustments=list(all_adjustments),
                total_amount=float(obj.sub_total.amount),
            )
            adjustment += adj_amount
            all_discounts = obj.discounts.all()
            disc_acmount, _ = cls._get_discounts_total(
                discounts=list(all_discounts),
                total_amount=float(obj.sub_total.amount),
            )
            discount += disc_acmount
            all_writeoffs = obj.writeoffs.all()
            wrt_amount, _ = cls._get_writeoffs_total(
                writeoffs=list(all_writeoffs),
                total_amount=float(obj.sub_total.amount),
            )
            writeoff += wrt_amount
            insurance += float(obj.insurance_amount.amount)
            other_fees += float(obj.other_fees.amount)
            tax += float(obj.tax.amount)
            tax_currency = obj.tax.currency
            adjustment_currency = (
                all_adjustments[0].amount.currency if len(all_adjustments) > 0 else None
            )
            discount_currency = (
                all_discounts[0].amount.currency if len(all_discounts) > 0 else None
            )
            writeoff_currency = (
                all_writeoffs[0].amount.currency if len(all_writeoffs) > 0 else None
            )
        return (
            tax,
            adjustment,
            discount,
            insurance,
            writeoff,
            other_fees,
            tax_currency,
            adjustment_currency,
            discount_currency,
            insurance_currency,
            writeoff_currency,
            other_fees_currency,
        )

    @classmethod
    def _get_static_summary(cls, instance, breakdowns):
        (
            tax,
            adjustment,
            discount,
            insurance,
            writeoff,
            other_fees,
            tax_currency,
            adjustment_currency,
            discount_currency,
            insurance_currency,
            writeoff_currency,
            other_fees_currency,
        ) = cls._calculate_static_summary(instance=instance, breakdowns=breakdowns)
        objs = []
        bill_id = instance.id
        cls._append_summary_data_obj(
            objs, bill_id, "Other Fees", other_fees, other_fees_currency
        )
        cls._append_summary_data_obj(
            objs, bill_id, "Adjustment", adjustment, adjustment_currency
        )
        cls._append_summary_data_obj(
            objs, bill_id, "Discount", -discount, discount_currency
        )
        cls._append_summary_data_obj(
            objs, bill_id, "Write-Off", -writeoff, writeoff_currency
        )
        cls._append_summary_data_obj(
            objs, bill_id, "Insurance", -insurance, insurance_currency
        )
        cls._append_summary_data_obj(objs, bill_id, "Tax", tax, tax_currency)
        if hasattr(instance, "pp") and instance.pp is not None:
            pp = instance.pp
            if pp.fees and float(pp.fees.amount) > 0:
                cls._append_summary_data_obj(
                    objs,
                    bill_id,
                    "Payment Plan Fees",
                    float(pp.fees.amount),
                    pp.fees.currency,
                )
            if pp.interest_amount and float(pp.interest_amount.amount) > 0:
                cls._append_summary_data_obj(
                    objs,
                    bill_id,
                    "Payment Plan Interest Amount",
                    float(pp.interest_amount.amount),
                    pp.interest_amount.currency,
                )
            if pp.tax and float(pp.tax.amount) > 0:
                cls._append_summary_data_obj(
                    objs,
                    bill_id,
                    "Payment Plan Tax",
                    float(pp.tax.amount),
                    pp.tax.currency,
                )
        return objs

    @classmethod
    def _append_summary_data_obj(
        cls, summary_objs, bill_id, title, amount, amount_currency
    ):
        summary_objs.append(
            cls._get_summary_data_obj(bill_id, title, amount, amount_currency)
        )

    @staticmethod
    def _get_summary_data_obj(bill_id, title, amount, amount_currency):
        return {
            "bill": bill_id,
            "title": title,
            "amount": amount,
            "amount_currency": amount_currency,
        }

    @staticmethod
    def _get_dynamic_summary(instance, breakdowns):
        categories = {}
        for obj in breakdowns:
            if summary := categories.get(obj.category_id):
                summary["amount"] += round(
                    float(obj.type_of_service_amount.amount) * obj.quantity, 2
                )
            else:
                summary = {
                    "bill": instance.id,
                    "title": obj.category_name,
                    "amount": round(
                        float(obj.type_of_service_amount.amount) * obj.quantity, 2
                    ),
                    "amount_currency": obj.type_of_service_amount.currency,
                }
            categories[obj.category_id] = summary
        return list(categories.values())

    @classmethod
    def build_summary_data(cls, instance, breakdowns):
        data = cls._get_dynamic_summary(instance=instance, breakdowns=breakdowns)
        data += cls._get_static_summary(instance=instance, breakdowns=breakdowns)
        return data
