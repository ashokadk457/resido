from collections import OrderedDict
from decimal import Decimal
from uuid import UUID

import pdfkit
from dateutil import parser
from django.template.loader import render_to_string

from common.utils.logging import logger
from common.utils.currency import get_currency_codes
from lookup.models import Lookup
from payments.models import Bill
from payments.serializers import BillDetailSerializer


class PaymentExport:
    TEMPLATE_FILE = "template.html"
    FORMAT_TO_CONTENT_TYPE = {
        "xml": "application/xhtml+xml",
        "html": "text/html",
        "pdf": "application/pdf",
        "7z": "application/x-7z-compressed",
    }

    def __init__(self, patient_id, bill_id):
        self.patient_id = str(patient_id)
        self.bill_id = bill_id

    def export_as_pdf(self):
        """
        Export the bill as a PDF file.
        """
        html_content = self._get_html_content()
        if html_content:
            return self._convert_html_to_pdf(html_content)
        return None

    def _get_html_content(self):
        """
        Load the HTML template and render it with the bill data.
        """
        try:
            export_request_obj = self._get_bill_object()
            html_content = render_to_string(self.TEMPLATE_FILE, export_request_obj)
            if not html_content.strip():
                raise ValueError("Rendered HTML is empty")
            return html_content
        except Exception as e:
            logger.error(f"Error loading HTML template: {str(e)}")
            return None

    @staticmethod
    def _convert_html_to_pdf(html_content):
        """
        Convert HTML content to PDF using pdfkit.
        """
        try:
            if not html_content:
                raise ValueError("HTML content is empty, cannot generate PDF.")
            pdf = pdfkit.from_string(html_content, False)
            if not pdf:
                raise ValueError("Failed to generate PDF.")
            return pdf
        except Exception as e:
            logger.error(f"Exception occurred while converting HTML to PDF: {str(e)}")
            return None

    def _get_bill_object(self):
        """
        Fetch the bill object and preprocess it for JSON serialization.
        """
        bill = Bill.objects.filter(id=self.bill_id).first()
        if not bill:
            raise Exception(f"No bill found with id {self.bill_id}")

        bill_obj = BillDetailSerializer(bill)
        processed_data = self._preprocess_data_for_json(bill_obj.data)
        processed_data = self._preprocess_ui_data(processed_data)
        processed_data = self._preprocess_amount(processed_data)
        processed_data = self._mask_and_format_data(processed_data)
        return self._group_breakdown_by_category(processed_data)

    @staticmethod
    def _preprocess_amount(data):
        """
        Preprocess the amount fields in the data dictionary.
        """
        total_amount = 0
        valid_breakdowns = []

        for breakdown in data.get("breakdown", []):
            if (
                not breakdown.get("category")
                or float(breakdown.get("patient_amount", 0)) == 0
            ):
                continue

            total_adjustment = round(
                sum(float(adj["amount"]) for adj in breakdown["adjustments"]), 2
            )
            total_write_off = round(
                sum(float(wri_off["amount"]) for wri_off in breakdown["writeoffs"]),
                2,
            )
            total_discounts = round(
                sum(float(dis["amount"]) for dis in breakdown["discounts"]), 2
            )
            breakdown["discount_amount"] = total_discounts
            breakdown["adjustment_amount"] = total_adjustment
            breakdown["write_off_amount"] = total_write_off

            valid_breakdowns.append(breakdown)

        data["breakdown"] = valid_breakdowns

        for summary in data.get("summary", []):
            amount = round(float(summary["amount"]), 2)
            summary["amount"] = amount
            total_amount += amount
        data["total_bill_amount"] = round(float(total_amount), 2)
        return data

    @staticmethod
    def _mask_and_format_data(data):
        """
        Mask sensitive data in the provided dictionary and format dates.
        """
        patient = data.get("patient", {})
        breakdowns = data.get("breakdown", [])

        status = str(data["status"]).split("_")
        data["status"] = " ".join([s.capitalize() for s in status]).strip()
        for breakdown in breakdowns:
            if service_start_date := breakdown.get("service_start_date"):
                breakdown["service_start_date"] = parser.parse(
                    service_start_date
                ).strftime("%m/%d/%Y")
            if service_end_date := breakdown.get("service_end_date"):
                breakdown["service_end_date"] = parser.parse(service_end_date).strftime(
                    "%m/%d/%Y"
                )

        if email := patient.get("email"):
            local, domain = email.split("@", 1)
            if len(local) > 4:
                masked_local = local[:4] + "x" * (len(local) - 4)
                patient["email"] = f"{masked_local}@{domain}"
            else:
                patient["email"] = email

        if (phone := patient.get("phone_number")) and len(phone) >= 4:
            patient["phone_number"] = "x" * (len(phone) - 4) + phone[-4:]

        if address := patient.get("address"):
            patient["address"] = address[0] + "x" * (len(address) - 2) + address[-1]

        if zipcode := patient.get("zipcode"):
            if len(zipcode) <= 2:
                patient["zipcode"] = zipcode[0] + "x" * (len(zipcode) - 1)
            else:
                patient["zipcode"] = zipcode[0] + "x" * (len(zipcode) - 2) + zipcode[-1]

        date_fields = [
            "service_start_date",
            "service_end_date",
            "statement_date",
            "due_date",
        ]
        for key in date_fields:
            if date_str := data.get(key):
                data[key] = parser.parse(date_str).strftime("%m/%d/%Y")

        if dob := patient.get("dob"):
            parsed_dob = parser.parse(dob).strftime("%m/%d/%Y")
            patient["dob"] = f"xx{parsed_dob[2:8]}xx"

        return data

    @staticmethod
    def _preprocess_ui_data(data):
        """
        Preprocess the data for UI display.
        """
        if data["status"] == "COMPLETED":
            data["status"] = "PAID"
            data["color"] = "#008069"
        else:
            data["color"] = "red"
        if data["payment_method"]:
            data["payment_method"] = (
                Lookup.objects.filter(
                    name="PAYMENT_METHODS", code=data["payment_method"]
                )
                .first()
                .value
            )
        currency_code = data.get("total_charges_currency")
        if currency_code:
            data["currency_symbol"] = get_currency_codes(currency_code)
        return data

    @staticmethod
    def _group_breakdown_by_category(data):
        """
        group breakdown by category and calculate totals for each category.
        """
        flat_list = data.get("breakdown", [])
        grouped = OrderedDict()

        for item in flat_list:
            category = item.get("category", {})
            category_id = category.get("id")
            if not category_id:
                continue
            category_name = item.get("category_name") or category.get("name")
            patient_amt = round(float(item.get("patient_amount") or 0), 2)
            sub_breakdown = {
                "id": item.get("id"),
                "service_name": item.get("type_of_service_name"),
                "start_date": item.get("service_start_date"),
                "end_date": item.get("service_end_date"),
                "quantity": item.get("quantity", 0),
                "unit_price": round(float(item.get("type_of_service_amount") or 0), 2),
                "insurance_amount": round(float(item.get("insurance_amount") or 0), 2),
                "adjustment_amount": round(
                    float(item.get("adjustment_amount") or 0), 2
                ),
                "discount_amount": round(float(item.get("discount_amount") or 0), 2),
                "tax": round(float(item.get("tax") or 0), 2),
                "other_fees": round(float(item.get("other_fees") or 0), 2),
                "write_off_amount": round(float(item.get("write_off_amount") or 0), 2),
                "total_amount": round(float(item.get("total_amount") or 0), 2),
                "patient_amount": patient_amt,
            }

            if category_id not in grouped:
                grouped[category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "services": [sub_breakdown],
                    "category_total": patient_amt,
                }
            else:
                group = grouped[category_id]
                group["services"].append(sub_breakdown)
                group["category_total"] += patient_amt

        data["breakdown"] = list(grouped.values())
        return data

    def _preprocess_data_for_json(self, data):
        """
        Preprocess data for JSON serialization and django template rendering.
        """
        if isinstance(data, dict):
            return {
                key: self._preprocess_data_for_json(value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._preprocess_data_for_json(item) for item in data]
        elif isinstance(data, UUID):
            return str(data)
        elif isinstance(data, Decimal):
            return str(data)
        else:
            return data
