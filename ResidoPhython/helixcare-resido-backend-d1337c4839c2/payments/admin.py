# from django.contrib import admin

# from common.utils.admin import PULSEBaseAdmin
# from payments.models import (
#     SavedAccount,
#     SavedCard,
#     Bill,
#     BillSummary,
#     Payment,
#     BillBreakDown,
#     PaymentPlan,
#     BillRefundRequest,
#     BillCancellationCodeComposition,
#     WriteOff,
#     Adjustment,
#     TransactionWriteOff,
#     TransactionAdjustment,
# )
# from payments.models_v2 import TransactionLog
# from payments.payment_constants import (
#     TransactionType,
#     CARD_BASED_TRANSACTION_METHODS,
#     TransactionMethod,
# )

# admin.site.register(BillSummary)
# admin.site.register(BillBreakDown)
# admin.site.register(PaymentPlan)


# @admin.register(WriteOff)
# class WriteOffAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "name",
#         "type_of_writeoff",
#         "value",
#         "max_upto",
#         "active",
#         "start_date",
#         "end_date",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("active", "type_of_writeoff")
#     search_fields = ("id", "name")


# @admin.register(Adjustment)
# class AdjustmentAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "name",
#         "type_of_adjustment",
#         "value",
#         "max_upto",
#         "active",
#         "start_date",
#         "end_date",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("active", "type_of_adjustment")
#     search_fields = ("id", "name")


# @admin.register(Bill)
# class BillAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "patient",
#         "provider",
#         "encounter",
#         "practice_location",
#     )

#     list_display = (
#         "id",
#         "display_id",
#         "patient_name",
#         "patient_amount",
#         "total_charges",
#         "insurance_paid",
#         "due_date_ist",
#         "paid_date_ist",
#         "cancellation_code",
#         "cancellation_reason",
#         "already_paid_amount_val",
#         "total_refunded_amount",
#         "total_refundable_amount",
#         "other_discount",
#         "other_adjustment",
#         "other_writeoff",
#         "other_tax",
#         "status",
#         "created_on_ist",
#         "updated_on_ist",
#         "transactions",
#         "refund_requests",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("status",)
#     search_fields = ("id", "display_id")

#     def paid_date_ist(self, obj):
#         return self._get_readable_timestamp(obj=obj, timestamp_field="paid_date")

#     def due_date_ist(self, obj):
#         return self._get_readable_timestamp(obj=obj, timestamp_field="due_date")

#     def transactions(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Transactions",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="payment",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def refund_requests(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Refund Requests",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="billrefundrequest",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def patient_name(self, obj):
#         if obj.patient is None:
#             return None

#         obj_id, link_text = str(obj.patient.id), str(obj.patient.name)

#         return self._get_admin_changelist_link(
#             app="residousers",
#             model="patient",
#             obj_id=obj_id,
#             link_text=link_text,
#         )


# @admin.register(Payment)
# class PaymentAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "bill",
#         "bill_refund_request",
#         "saved_account",
#         "saved_card",
#         "parent",
#     )
#     list_display = (
#         "id",
#         "display_id",
#         "bill_id",
#         "bill_refund_request_id",
#         "transaction_type",
#         "parent_txn",
#         "transaction_id",
#         "order_id",
#         "amount",
#         "refund_amount",
#         "refundable_amount",
#         "method",
#         "card_info",
#         "account_info",
#         "payment_plan",
#         "write_off_obj",
#         "adjustment_obj",
#         "status",
#         "gateway_status",
#         "gateway_recon_last_request_id",
#         "gateway_status_last_updated_on_ist",
#         "created_on_ist",
#         "updated_on_ist",
#         "logs",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = (
#         "payment_method",
#         "status",
#         "transaction_type",
#         "write_off_amount_overridden",
#         "adjustment_amount_overridden",
#         "gateway_status",
#     )
#     search_fields = (
#         "id",
#         "bill__id",
#         "bill_refund_request__id",
#         "gateway_recon_last_request_id",
#     )

#     def gateway_status_last_updated_on_ist(self, obj):
#         return self._get_readable_timestamp(
#             obj=obj, timestamp_field="gateway_status_last_updated_on"
#         )

#     def logs(self, obj):
#         return self._get_admin_changelist_link(
#             app="payments",
#             model="transactionlog",
#             obj_id=str(obj.id),
#             link_text="Check Logs",
#         )

#     def card_info(self, obj):
#         if (obj.transaction_type == TransactionType.REFUND.value) or (
#             obj.method not in CARD_BASED_TRANSACTION_METHODS
#         ):
#             return None

#         if obj.method == TransactionMethod.POS_PAYMENT.value:
#             return obj.card_info

#         try:
#             saved_card_id, link_text = str(obj.saved_card.id), obj.card_info
#             if not saved_card_id:
#                 return saved_card_id

#             return self._get_admin_changelist_link(
#                 app="payments",
#                 model="savedcard",
#                 obj_id=saved_card_id,
#                 link_text=link_text,
#             )
#         except Exception:
#             return None

#     def account_info(self, obj):
#         if obj.saved_account is None:
#             return None

#         try:
#             saved_account_id, link_text = str(obj.saved_account.id), obj.account_info
#             if not saved_account_id:
#                 return saved_account_id

#             return self._get_admin_changelist_link(
#                 app="payments",
#                 model="savedaccount",
#                 obj_id=saved_account_id,
#                 link_text=link_text,
#             )
#         except Exception:
#             return None

#     @staticmethod
#     def refundable_amount(obj):
#         return obj.refundable_amount

#     def bill_id(self, obj):
#         if obj.bill is None:
#             return None

#         bill_id, link_text = str(obj.bill.id), str(obj.bill.display_id)
#         if not bill_id:
#             return bill_id

#         return self._get_admin_changelist_link(
#             app="payments", model="bill", obj_id=bill_id, link_text=link_text
#         )

#     def parent_txn(self, obj):
#         if obj.parent is None:
#             return None

#         parent_id, link_text = str(obj.parent.id), str(obj.parent.display_id)
#         return self._get_admin_changelist_link(
#             app="payments", model="payment", obj_id=parent_id, link_text=link_text
#         )

#     def write_off_obj(self, obj):
#         if obj.write_off is None:
#             return None

#         write_off_id, link_text = str(obj.write_off.id), str(obj.write_off.__str__())
#         return self._get_admin_changelist_link(
#             app="payments", model="writeoff", obj_id=write_off_id, link_text=link_text
#         )

#     def adjustment_obj(self, obj):
#         if obj.adjustment is None:
#             return None

#         adjustment_obj_id, link_text = str(obj.adjustment.id), str(
#             obj.adjustment.__str__()
#         )
#         return self._get_admin_changelist_link(
#             app="payments",
#             model="adjustment",
#             obj_id=adjustment_obj_id,
#             link_text=link_text,
#         )

#     def bill_refund_request_id(self, obj):
#         if obj.bill_refund_request is None:
#             return None

#         bill_refund_request_id, link_text = str(obj.bill_refund_request.id), str(
#             obj.bill_refund_request.display_id
#         )

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="billrefundrequest",
#             obj_id=bill_refund_request_id,
#             link_text=link_text,
#         )


# @admin.register(TransactionLog)
# class TransactionLogAdmin(PULSEBaseAdmin):
#     readonly_fields = (
#         "created_by",
#         "updated_by",
#         "deleted_by",
#         "transaction",
#         "source",
#         "event",
#         "data",
#         "request_id",
#     )
#     list_display = (
#         "id",
#         "request_id",
#         "txn",
#         "event",
#         "source",
#         "data",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     list_filter = ("event", "source")
#     ordering = ["-created_on"]
#     list_per_page = 25
#     search_fields = (
#         "id",
#         "request_id",
#         "transaction__id",
#         "transaction__display_id",
#     )

#     def txn(self, obj):
#         if obj.transaction is None:
#             return None

#         transaction_id, link_text = str(obj.transaction.id), str(
#             obj.transaction.display_id
#         )
#         if not transaction_id:
#             return transaction_id

#         return self._get_admin_changelist_link(
#             app="payments", model="payment", obj_id=transaction_id, link_text=link_text
#         )


# @admin.register(BillRefundRequest)
# class BillRefundRequestAdmin(PULSEBaseAdmin):
#     readonly_fields = ("created_by", "updated_by", "deleted_by", "bill", "process")
#     list_display = (
#         "id",
#         "display_id",
#         "bill_id",
#         "refund_reason",
#         "refund_type",
#         "total_refund_requested",
#         "total_refund_processed",
#         "process_id",
#         "status",
#         "created_on_ist",
#         "updated_on_ist",
#         "refund_transactions",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("refund_type", "status")
#     search_fields = ("id", "bill__id")

#     def bill_id(self, obj):
#         bill_id, link_text = str(obj.bill.id), str(obj.bill.display_id)
#         if not bill_id:
#             return bill_id

#         return self._get_admin_changelist_link(
#             app="payments", model="bill", obj_id=bill_id, link_text=link_text
#         )

#     def refund_transactions(self, obj):
#         _obj_id, link_text = (
#             str(obj.id),
#             "View Refund Transactions",
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="payment",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def process_id(self, obj):
#         _obj_id, link_text = str(obj.process_id), str(obj.process_id)
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="processflow", model="process", obj_id=_obj_id, link_text=link_text
#         )


# @admin.register(BillCancellationCodeComposition)
# class BillCancellationCodeCompositionAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "cancellation_code",
#         "cancellation_reason",
#         "active",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("active", "cancellation_code", "cancellation_reason")
#     search_fields = ("id",)


# @admin.register(TransactionWriteOff)
# class TransactionWriteOffAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "transaction_obj",
#         "write_off_object",
#         "name",
#         "type_of_writeoff",
#         "value",
#         "max_upto",
#         "amount",
#         "taxable",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("type_of_writeoff", "taxable")
#     search_fields = ("id", "transaction__id", "name", "write_off_obj__id")

#     def transaction_obj(self, obj):
#         _obj_id, link_text = (
#             str(obj.transaction.id),
#             obj.transaction.display_id,
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="payment",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def write_off_object(self, obj):
#         if obj.write_off_obj is None:
#             return None

#         write_off_id, link_text = str(obj.write_off_obj.id), str(obj.write_off_obj.id)
#         return self._get_admin_changelist_link(
#             app="payments", model="writeoff", obj_id=write_off_id, link_text=link_text
#         )


# @admin.register(TransactionAdjustment)
# class TransactionAdjustmentAdmin(PULSEBaseAdmin):
#     list_display = (
#         "id",
#         "transaction_obj",
#         "adjustment_obj",
#         "name",
#         "type_of_adjustment",
#         "value",
#         "max_upto",
#         "amount",
#         "taxable",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("type_of_adjustment", "taxable")
#     search_fields = ("id", "transaction__id", "name", "adj_obj__id")

#     def transaction_obj(self, obj):
#         _obj_id, link_text = (
#             str(obj.transaction.id),
#             obj.transaction.display_id,
#         )
#         if not _obj_id:
#             return _obj_id

#         return self._get_admin_changelist_link(
#             app="payments",
#             model="payment",
#             obj_id=_obj_id,
#             link_text=link_text,
#         )

#     def adjustment_obj(self, obj):
#         if obj.adj_obj is None:
#             return None

#         adj_obj_id, link_text = str(obj.adj_obj_id.id), str(obj.adj_obj_id.id)
#         return self._get_admin_changelist_link(
#             app="payments", model="adjustment", obj_id=adj_obj_id, link_text=link_text
#         )


# @admin.register(SavedCard)
# class SavedCardAdmin(PULSEBaseAdmin):
#     readonly_fields = ("created_by", "updated_by", "deleted_by", "patient")
#     list_display = (
#         "id",
#         "patient_name",
#         "card_type",
#         "last_4_digits",
#         "primary_method",
#         "data_encrypted",
#         "user_representation",
#         "active",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("card_type", "primary_method", "data_encrypted", "active")
#     search_fields = ("id", "patient__id")

#     def patient_name(self, obj):
#         if obj.patient is None:
#             return None

#         obj_id, link_text = str(obj.patient.id), str(obj.patient.name)

#         return self._get_admin_changelist_link(
#             app="residousers",
#             model="patient",
#             obj_id=obj_id,
#             link_text=link_text,
#         )


# @admin.register(SavedAccount)
# class SavedAccountAdmin(PULSEBaseAdmin):
#     readonly_fields = ("created_by", "updated_by", "deleted_by", "patient")
#     list_display = (
#         "id",
#         "patient_name",
#         "account_type",
#         "routing_number",
#         "account_number",
#         "last_4_digits",
#         "primary_method",
#         "data_encrypted",
#         "user_representation",
#         "active",
#         "created_on_ist",
#         "updated_on_ist",
#     )
#     ordering = ["-created_on"]
#     list_per_page = 25
#     list_filter = ("account_type", "primary_method", "data_encrypted", "active")
#     search_fields = ("id", "patient__id")

#     def patient_name(self, obj):
#         if obj.patient is None:
#             return None

#         obj_id, link_text = str(obj.patient.id), str(obj.patient.name)

#         return self._get_admin_changelist_link(
#             app="residousers",
#             model="patient",
#             obj_id=obj_id,
#             link_text=link_text,
#         )
