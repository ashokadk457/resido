import django_filters
import time
from datetime import datetime
import base64

from rest_framework.permissions import AllowAny

from common.errors import ERROR_DETAILS
from payments.filters.refund import BillRefundRequestFilter
from payments.helix_payment_processor import HelixPaymentProcessor
from payments.managers.bill_pp import BillPaymentPlanManager
from payments.models import (
    Bill,
    Payment,
    SavedAccount,
    SavedCard,
    Category,
    SubCategory,
    Discount,
    TaxPerState,
    TypeOfService,
    PaymentPlan,
    BillPaymentPlan,
    WriteOff,
    Adjustment,
    BillRefundRequest,
    BillCancellationCodeComposition,
)

from payments.serializers import (
    BillDetailSerializer,
    BillBreakDownSerializer,
    PaymentSerializer,
    BillListSerializer,
    SavedCardSerializer,
    SavedAccountSerializer,
    CategoryDetailSerializer,
    CategoryListSerializer,
    DiscountSerializer,
    TaxPerStateSerializer,
    SubCategoryListSerializer,
    SubCategoryDetailSerializer,
    TypeOfServiceSerializer,
    PaymentLinkGenerationSerializer,
    PaymentPlanSerializer,
    BillPaymentPlanSerializer,
    BillPaymentPlanDetailSerializer,
    BillRefundRequestSerializer,
    BillCancellationCodeCompositionSerializer,
)
from payments.serializers_v2 import AdjustmentSerializer, WriteOffSerializer
from common.mixins import (
    StandardListCreateAPIMixin,
    StandardRetrieveUpdateAPIMixin,
    StandardRetieveAPIMixin,
    StandardListAPIMixin,
    CountAPIMixin,
)
from common.utils.logging import logger
from common.utils.currency import get_currency_codes
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from common.permissions import (
    HelixUserBasePermission,
    IsAuthenticatedResidentPermission,
)
from common.exception import StandardAPIException
from common.response import StandardAPIResponse
from rest_framework.exceptions import APIException

from payments.filters.bill import BillFilter
from payments.filters.transaction import TransactionFilter
from payments.managers.bill.core import BillManager
from .filters.bccc import BillCancellationCodeCompositionFilter
from payments.managers.transaction.core import TransactionManager
from .payment_export import PaymentExport
from .managers.calculator.discounts import DiscountCalculator
from .payment_constants import (
    PAYMENT_LINK_MAIL_SUBJECT,
    PAYMENT_LINK_MAIL_BODY,
    PAYMENT_LINK_TEMPLATE_URL,
    TransactionMethod,
    TransactionStatus,
)
from payments.utils import filter_by_date_range, filter_by_id
from helixauth.constants import DEFAULT_COUNTRY_CODE
from notifications.utils import get_resident_communication_details
from connecthub.managers import managers
from customer_backend.managers.tenant import TenantManager
from lookup.models import Lookup


class BillListView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Bill"
    allowed_methods_to_resident = {"get": True}
    search_fields = (
        "display_id",
        "patient__patient_id",
        "service",
        "patient__first_name",
        "patient__last_name",
    )
    filterset_class = BillFilter

    def get_queryset(self):
        return Bill.objects.for_current_user().order_by("-created_on")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BillDetailSerializer
        return BillListSerializer

    @classmethod
    def _pass_on_location_id_to_leaf_nodes(cls, data):
        location_id = data.get("practice_location_id", None)
        if not location_id:
            return data
        breakdowns = data.get("breakdown", [])
        breakdowns = cls._append_data_to_all_childs(
            breakdowns, "practice_location_id", location_id
        )
        data["breakdown"] = breakdowns
        return data

    @staticmethod
    def _append_data_to_all_childs(childs, key, value):
        for c in childs:
            c[key] = value
        return childs

    def create(self, request, *args, **kwargs):
        data = request.data
        data = self._pass_on_location_id_to_leaf_nodes(data=data)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class BillDetailView(StandardRetrieveUpdateAPIMixin):
    serializer_class = BillDetailSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Bill"
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        return Bill.objects.for_current_user()


class SavedCardListView(StandardListCreateAPIMixin):
    serializer_class = SavedCardSerializer
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "SavedCard"
    filter_backends = (DjangoFilterBackend,)
    filter_fields = (
        "patient",
        "active",
        "primary_method",
    )

    def get_queryset(self):
        query = SavedCard.objects.for_current_user().order_by("-created_on")
        if self.kwargs.get("patient_id"):
            query = query.filter(patient_id=self.kwargs.get("patient_id"))
        return query.order_by("-primary_method", "-created_on")


class SavedCardDetailView(StandardRetrieveUpdateAPIMixin, GenericAPIView):
    serializer_class = SavedCardSerializer
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "SavedCard"

    def get_queryset(self):
        query = SavedCard.objects.for_current_user()
        if self.kwargs.get("patient_id"):
            query = query.filter(patient_id=self.kwargs.get("patient_id"))
        return query.order_by("-primary_method", "-created_on")

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_by = request.user
        instance.save()
        return StandardAPIResponse(data=None, status=status.HTTP_204_NO_CONTENT)


class SavedAccountListView(StandardListCreateAPIMixin):
    serializer_class = SavedAccountSerializer
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "SavedAccount"
    filter_backends = (DjangoFilterBackend,)
    filter_fields = (
        "patient",
        "active",
        "primary_method",
    )

    def get_queryset(self):
        query = SavedAccount.objects.for_current_user().order_by("-created_on")
        if self.kwargs.get("patient_id"):
            query = query.filter(patient_id=self.kwargs.get("patient_id"))
        return query.order_by("-primary_method", "-created_on")


class SavedAccountDetailView(StandardRetrieveUpdateAPIMixin, GenericAPIView):
    serializer_class = SavedAccountSerializer
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "SavedAccount"

    def get_queryset(self):
        query = SavedAccount.objects.for_current_user()
        if self.kwargs.get("patient_id"):
            query = query.filter(patient_id=self.kwargs.get("patient_id"))
        return query.order_by("-primary_method", "-created_on")

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_by = request.user
        instance.save()
        return StandardAPIResponse(data=None, status=status.HTTP_204_NO_CONTENT)


class PaymentListView(StandardListCreateAPIMixin):
    serializer_class = PaymentSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Payment"
    allowed_methods_to_resident = {"get": True}
    filter_class = TransactionFilter
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    search_fields = (
        "display_id",
        "order_id",
        "bill__display_id",
        "bill__patient__patient_id",
        "bill_refund_request__display_id",
        "bill__patient__first_name",
        "bill__patient__last_name",
    )

    def get_queryset(self):
        queryset = Payment.objects.for_current_user().select_related(
            "bill", "bill__patient", "bill__encounter", "bill__provider"
        )
        if self.kwargs.get("bill_id"):
            queryset = queryset.filter(bill_id=self.kwargs.get("bill_id"))
        return queryset


class PaymentDetailView(StandardRetrieveUpdateAPIMixin):
    serializer_class = PaymentSerializer
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Payment"
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        return Payment.objects.for_current_user().filter(
            bill_id=self.kwargs.get("bill_id")
        )


class PayBillAPIView(APIView):
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "Payment"

    @staticmethod
    def get_validated_payment_method(payment_method):
        if payment_method in TransactionMethod.values():
            return payment_method

        raise StandardAPIException(
            code="invalid_payment_method",
            detail=ERROR_DETAILS["invalid_payment_method"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def post(self, request):
        request_data = request.data
        bill_id = request_data.pop("bill", None)
        amount = request_data.pop("amount", None)
        payment_method = request_data.pop("payment_method", None)
        payment_plan_id = request_data.pop("payment_plan_id", None)
        payment_term = request_data.pop("payment_term", None)
        installment_date = request_data.pop("installment_date", None)
        saved_card_id = request_data.pop("saved_card", None)
        card = request_data.pop("card", None)
        saved_account_id = request_data.pop("saved_account", None)
        account = request_data.pop("account", None)
        cvv = request_data.pop("cvv", None)
        saved_card = None
        saved_account = None
        payment_method = self.get_validated_payment_method(
            payment_method=payment_method
        )
        try:
            bill = Bill.objects.for_current_user().get(id=bill_id)
            if bill.status == "COMPLETED":
                raise StandardAPIException(
                    code="payment_done",
                    detail=ERROR_DETAILS["payment_done"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if bill.status not in ["PENDING", "PARTIALLY_COMPLETED"]:
                raise StandardAPIException(
                    code="invalid_status",
                    detail=ERROR_DETAILS["invalid_status"].format(entity="Bill"),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        except Bill.DoesNotExist:
            raise StandardAPIException(
                code="bill_not_found",
                detail=ERROR_DETAILS["bill_not_found"],
                status_code=status.HTTP_404_NOT_FOUND,
            )
        if payment_method in ["CREDIT_CARD", "DEBIT_CARD"]:
            if not saved_card_id and not card:
                raise StandardAPIException(
                    code="card_missing_payment",
                    detail=ERROR_DETAILS["card_missing_payment"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if saved_card_id:
                try:
                    saved_card = SavedCard.objects.get(
                        id=saved_card_id, patient=bill.patient
                    )
                except SavedCard.DoesNotExist:
                    raise StandardAPIException(
                        code="card_not_found",
                        detail=ERROR_DETAILS["card_not_found"],
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
            else:
                card_srz = SavedCardSerializer(data=card)
                card_srz.is_valid(raise_exception=True)
                card_data = card_srz.data
                card_data["patient_id"] = card_data.pop("patient")
                saved_card = SavedCard(**card_data)
        elif payment_method == "BANK_TRANSFER":
            if not saved_account_id and not account:
                raise StandardAPIException(
                    code="account_missing_payment",
                    detail=ERROR_DETAILS["account_missing_payment"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if saved_account_id:
                try:
                    saved_account = SavedAccount.objects.get(
                        id=saved_account_id, patient=bill.patient
                    )
                except SavedAccount.DoesNotExist:
                    raise StandardAPIException(
                        code="account_not_found",
                        detail=ERROR_DETAILS["account_not_found"],
                        status_code=status.HTTP_404_NOT_FOUND,
                    )
            else:
                acc_srz = SavedAccountSerializer(data=account)
                acc_srz.is_valid(raise_exception=True)
                acc_data = acc_srz.data
                acc_data["patient_id"] = acc_data.pop("patient")
                saved_account = SavedAccount(**acc_data)

        already_paid_amount = Payment.objects.filter(
            bill=bill, status="COMPLETED"
        ).aggregate(total=Sum("amount"))["total"]

        already_paid_amount = (
            0 if not already_paid_amount else float(already_paid_amount)
        )

        pending_amount = float(bill.patient_amount.amount) - already_paid_amount

        if amount is None:
            amount = pending_amount

        if (
            float(amount) <= 0.00
            or float(amount) > pending_amount
            or (payment_term and float(amount) != float(bill.patient_amount.amount))
        ):
            raise StandardAPIException(
                code="invalid_amount",
                detail=ERROR_DETAILS["invalid_amount"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if cvv is None and payment_method in ["CREDIT_CARD", "DEBIT_CARD"]:
            raise StandardAPIException(
                code="invalid_cvv",
                detail=ERROR_DETAILS["invalid_cvv"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if payment_plan_id:
            try:
                pp = PaymentPlan.objects.get(id=payment_plan_id)
            except Exception:
                raise StandardAPIException(
                    code="invalid_id",
                    detail=ERROR_DETAILS["invalid_id"].format(param="Payment Plan"),
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            payment_term = pp.duration
        else:
            payment_term = None

        payment_plan = "monthly"
        if payment_term is None:
            payment_plan = "full"

        if payment_plan == "monthly" and installment_date is None:
            raise StandardAPIException(
                code="invalid_installment_date",
                detail=ERROR_DETAILS["invalid_installment_date"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if installment_date:
            try:
                installment_date = datetime.strptime(installment_date, "%d-%m-%Y")
            except ValueError:
                raise StandardAPIException(
                    code="invalid_installment_date",
                    detail=ERROR_DETAILS["invalid_installment_date"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if payment_plan_id and payment_method in [
            "CREDIT_CARD",
            "DEBIT_CARD",
            "BANK_TRANSFER",
        ]:
            consent = BillPaymentPlanManager(
                bill=bill,
                payment_plan=pp,
                payment_method=payment_method,
                pp_start_date=installment_date,
                cvv=cvv,
                card=saved_card,
                account=saved_account,
                save_method=saved_card_id is not None or saved_account_id is not None,
            )
            success, resp, error_code, error_message = consent.process_consent()
            if not success:
                raise StandardAPIException(
                    code=error_code,
                    detail=error_message,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            return StandardAPIResponse(data=resp, status=status.HTTP_200_OK)

        try:
            payment = Payment.objects.create(
                order_id=f"PAY-{int(time.time())}",
                amount=amount,
                bill=bill,
                payment_method=payment_method,
                status="PENDING",
                saved_card=saved_card if saved_card_id else None,
                saved_account=saved_account if saved_account_id else None,
                payment_term=payment_term,
                payment_plan=payment_plan,
                installment_date=installment_date,
            )

            payment_process_data = HelixPaymentProcessor.process_payment(
                payment, cvv, payment_term, installment_date, saved_card, saved_account
            )
            return Response(
                {
                    "message": payment_process_data.pop("message", None),
                    "payment_id": str(payment.id),
                    "extra_data": payment_process_data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Bill.DoesNotExist:
            raise StandardAPIException(
                code="bill_not_found",
                detail=ERROR_DETAILS["bill_not_found"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except APIException as api_exc:
            logger.error(f"Payment processing failed: {api_exc}")
            raise StandardAPIException(
                code="error_payment",
                detail=api_exc,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.info(f"Exception occurred while reading versions data: {str(exc)}")
            raise StandardAPIException(
                code="error_payment",
                detail=ERROR_DETAILS["error_payment"],
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CancelTransactionAPIView(APIView):
    permission_classes = [IsAuthenticatedResidentPermission]

    def post(self, request, *args, **kwargs):
        request_data = request.data
        bill_id = request_data.get("bill")

        if not bill_id:
            raise StandardAPIException(
                code="missing_bill_id",
                detail=ERROR_DETAILS["missing_bill_id"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bill = Bill.objects.get(id=bill_id)
        except Payment.DoesNotExist:
            raise StandardAPIException(
                code="bill_not_found",
                detail=ERROR_DETAILS["bill_not_found"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bill_manager = BillManager(bill_obj=bill, bill_id=bill_id)
            cancel_response = bill_manager.cancel_last_open_transaction()
            if not cancel_response.get("success", False):
                logger.error(f"Cancellation failed: response > {cancel_response}")
                raise StandardAPIException(
                    code="cancel_error",
                    detail=f"{cancel_response}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            return StandardAPIResponse(data=cancel_response, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.error(f"Unexpected error during cancellation: {str(exc)}")
            raise StandardAPIException(
                code="internal_server_error",
                detail=f"{str(exc)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CategoryListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    queryset = Category.objects.all()
    entity = "Category"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    ordering = ("-created_on",)
    search_fields = ("name",)
    filter_fields = ("active",)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CategoryDetailSerializer
        return CategoryListSerializer


class CategoryGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = CategoryDetailSerializer
    queryset = Category.objects.all().prefetch_related(
        "sub_category", "sub_category__type_of_service"
    )
    entity = "Category"
    allowed_methods_to_resident = {"get": True}


class SubCategoryListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    queryset = SubCategory.objects.all().select_related("category")
    entity = "SubCategory"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    ordering = ("-created_on",)
    search_fields = ("name",)
    filter_fields = ("active", "category")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SubCategoryDetailSerializer
        return SubCategoryListSerializer


class SubCategoryGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = SubCategoryListSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = SubCategory.objects.all().select_related("category")
    entity = "SubCategory"


class TypeOfServiceListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = TypeOfServiceSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = TypeOfService.objects.all().select_related(
        "sub_category", "sub_category__category"
    )
    entity = "TypeOfService"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    ordering = ("-created_on",)
    search_fields = ("name",)
    filter_fields = ("active", "sub_category", "taxable")


class TypeOfServiceGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = TypeOfServiceSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = TypeOfService.objects.all().select_related(
        "sub_category", "sub_category__category"
    )
    entity = "TypeOfService"


def search_for_lookup_fields(search_text: str, lookup_filters: dict, queryset):
    # TODO: move this to utils or lookup manager
    if search_text:
        lookup_qs = Lookup.objects.filter(
            name__in=lookup_filters.keys(),
            active=True,
            display_name__icontains=search_text,
        )
        lookup_codes = lookup_qs.values_list("code", flat=True)

        q_objects = Q()
        for lookup_filter in lookup_filters.values():
            q_objects |= Q(**{f"{lookup_filter}__in": lookup_codes})

        return queryset.filter(q_objects)
    return queryset


class TaxPerStateListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = TaxPerStateSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = TaxPerState.objects.all()
    entity = "TaxPerState"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering = ("-created_on",)
    search_lookup_fields = {"STATE": "state", "COUNTRY": "country"}
    filterset_fields = ["state", "tax_type", "active"]

    def get_queryset(self):
        search = self.request.query_params.get("search", "").strip()
        if search:
            self.queryset = search_for_lookup_fields(
                search, self.search_lookup_fields, self.queryset
            )
        return self.queryset


class TaxPerStateGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = TaxPerStateSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = TaxPerState.objects.all()
    entity = "TaxPerState"


class DiscountFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(lookup_expr="gte")
    end_date = django_filters.DateFilter(lookup_expr="gte")

    class Meta:
        model = Discount
        fields = (
            "active",
            "type_of_discount",
            "start_date",
            "end_date",
        )


class DiscountListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = DiscountSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = Discount.objects.for_current_user()
    entity = "Discount"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    search_fields = ("name",)
    filterset_class = DiscountFilter

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = filter_by_date_range(
            queryset=queryset,
            valid_from_date=self.request.query_params.get("valid_from"),
            valid_to_date=self.request.query_params.get("valid_to"),
        )
        return queryset.order_by("-updated_on")


class DiscountGetUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = DiscountSerializer
    allowed_methods_to_resident = {"get": True}
    queryset = Discount.objects.for_current_user()
    entity = "Discount"


class DiscountCountAPIView(CountAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    entity = "Discount"
    queryset = Discount.objects.for_current_user()
    count_label_to_field_condition_map = {
        "all": {"field": "id", "condition": {}},
        "active": {"field": "active", "condition": {"active": True}},
        "inactive": {"field": "active", "condition": {"active": False}},
    }


class ExportPaymentPDFView(APIView):
    permission_classes = [IsAuthenticatedResidentPermission]
    entity = "Payment"

    @staticmethod
    def post(request, bill_id):
        try:
            patient_id = request.data.get("patient_id")
            if not patient_id:
                raise StandardAPIException(
                    code="patient_id_missing",
                    detail=ERROR_DETAILS["patient_id_missing"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            if not bill_id:
                raise StandardAPIException(
                    code="bill_not_found",
                    detail=ERROR_DETAILS["bill_not_found"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            payment_export = PaymentExport(patient_id, bill_id)
            pdf_result = payment_export.export_as_pdf()
            if pdf_result:
                base64_encoded_pdf = base64.b64encode(pdf_result)
                response_data = {
                    "file_name": f"{patient_id}_{bill_id}_payment_export.pdf",
                    "file_data": base64_encoded_pdf,
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Failed to generate the PDF."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BillBreakdownCalculationAPIView(GenericAPIView):
    permission_classes = [HelixUserBasePermission]
    entity = "BillBreakDown"

    def post(self, request, *args, **kwargs):
        srz = BillBreakDownSerializer(data=request.data)
        srz.is_valid(raise_exception=True)

        response_data = {
            "total_amount": srz.validated_data.get("total_amount"),
            "patient_amount": srz.validated_data.get("patient_amount"),
            "tax": srz.validated_data.get("tax"),
        }

        # Convert currency codes to symbols
        for currency_field in [
            "total_amount_currency",
            "patient_amount_currency",
            "tax_currency",
        ]:
            currency_code = srz.validated_data.get(currency_field)
            if currency_code:
                response_data[currency_field] = get_currency_codes(currency_code)
            else:
                response_data[currency_field] = currency_code

        return StandardAPIResponse(
            data=response_data,
            status=status.HTTP_200_OK,
        )


class BillDiscountCalculationAPIView(GenericAPIView):
    permission_classes = [HelixUserBasePermission]
    entity = "Discount"
    queryset = Discount.objects.all()

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            amount = float(request.data.get("amount"))
        except Exception:
            raise StandardAPIException(
                code="invalid_input_value",
                detail=ERROR_DETAILS["invalid_input_value"].format(param="amount"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        manager = DiscountCalculator(discount_obj=obj, amount=amount)
        discount = manager.calculate_discount()
        return StandardAPIResponse(
            data={"discount": discount}, status=status.HTTP_200_OK
        )


class BillCountView(GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "Bill"

    def get(self, request, *args, **kwargs):
        patient_id = request.query_params.get("patient_id", None)
        query = Bill.objects.for_current_user()
        if patient_id:
            query = query.filter(patient_id=patient_id)
        data = list(query.values("status").annotate(count=Count("status")))
        required_status_count = {
            "PENDING": 0,
            "PARTIALLY_COMPLETED": 0,
            "PAYMENT_PLAN": 0,
            "COMPLETED": 0,
            "FAILED": 0,
            "REFUNDED": 0,
            "REFUND_INITIATED": 0,
            "PARTIAL_REFUND_INITIATED": 0,
            "PARTIAL_REFUND_FAILED": 0,
            "REFUND_FAILED": 0,
            "PARTIALLY_REFUNDED": 0,
            "CANCELLED": 0,
            "TOTAL": 0,
        }
        for obj in data:
            if required_status_count.get(obj["status"]) is not None:
                required_status_count[obj["status"]] += obj["count"]
                required_status_count["TOTAL"] += obj["count"]
        bpp = BillPaymentPlan.objects.all()
        if patient_id:
            bpp = bpp.filter(bill__patient_id=patient_id)
        required_status_count["PAYMENT_PLAN"] = bpp.count()
        required_status_count["TOTAL"] += required_status_count["PAYMENT_PLAN"]
        refund_related_statuses = [
            "REFUND_INITIATED",
            "PARTIAL_REFUND_INITIATED",
            "PARTIAL_REFUND_FAILED",
            "REFUND_FAILED",
            "PARTIALLY_REFUNDED",
        ]
        required_status_count["REFUNDED"] += sum(
            required_status_count[_status] for _status in refund_related_statuses
        )

        return StandardAPIResponse(
            data=required_status_count, status=status.HTTP_200_OK
        )


class PaymentCountView(GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "payment"

    def get(self, request, *args, **kwargs):
        patient_id = request.query_params.get("patient_id", None)

        payment_queryset = Payment.objects.all()
        if patient_id:
            payment_queryset = payment_queryset.filter(bill__patient__id=patient_id)

        status_counts = payment_queryset.values("status").annotate(count=Count("id"))

        status_summary = {entry["status"]: entry["count"] for entry in status_counts}
        for transaction_status in TransactionStatus:
            status_summary.setdefault(transaction_status.name, 0)

        status_summary["TOTAL"] = payment_queryset.count()

        return StandardAPIResponse(data=status_summary, status=status.HTTP_200_OK)


class PaymentMethodsCountView(GenericAPIView):
    permission_classes = [IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    entity = "payment"

    def get(self, request, *args, **kwargs):
        user = request.user

        totals = {
            "total_saved_cards": SavedCard.objects.filter(
                patient__user=user, active=True
            ).count()
            or 0,
            "total_saved_accounts": SavedAccount.objects.filter(
                patient__user=user, active=True
            ).count()
            or 0,
        }

        return StandardAPIResponse(data=totals, status=status.HTTP_200_OK)


class PaymentLinkGeneration(StandardRetieveAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    serializer_class = PaymentLinkGenerationSerializer
    entity = "Bill"
    allowed_methods_to_resident = {"get": True}

    def get_queryset(self):
        return Bill.objects.for_current_user()


class PaymentPlanListCreateView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerializer
    allowed_methods_to_resident = {"get": True}
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    entity = "PaymentPlan"
    search_fields = ["name"]
    filterset_fields = ["name", "active"]


class PaymentPlanRetrieveUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = PaymentPlan.objects.all()
    entity = "PaymentPlan"
    serializer_class = PaymentPlanSerializer
    allowed_methods_to_resident = {"get": True}


class SharePaymentLinkAPIView(GenericAPIView):
    permission_classes = [
        HelixUserBasePermission,
    ]
    entity = "Bill"
    queryset = Bill.objects.all()
    email_creator = managers.EmailManager()
    sms_creator = managers.SMSManager()

    def get_payment_body(self, bill_id, uid):
        domain = TenantManager().tenant_obj.domain
        payment_link = PAYMENT_LINK_TEMPLATE_URL.format(
            domain=domain, bill_id=bill_id, uid=uid
        )
        return PAYMENT_LINK_MAIL_BODY.format(PAYMENT_LINK_TEMPLATE_URL=payment_link)

    def trigger_payment_link(self, request_data):
        bill_object = self.get_object()
        response_user_ids = []
        notification_type = request_data["communication_mode"]
        subject = PAYMENT_LINK_MAIL_SUBJECT
        patient_obj = bill_object.patient.id
        message = self.get_payment_body(bill_id=bill_object.id, uid=patient_obj)
        email, phone_number, _country_code = get_resident_communication_details(
            id=str(patient_obj)
        )
        if not email or not phone_number:
            raise StandardAPIException(
                code="invalid_communication_details",
                detail=ERROR_DETAILS["invalid_communication_details"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        country_code = DEFAULT_COUNTRY_CODE
        country_code = country_code if not _country_code else _country_code
        receiving_address = f"{country_code}{phone_number}"
        if any("email" == item.lower() for item in notification_type) and any(
            "sms" == item.lower() for item in notification_type
        ):
            response_email = self.email_creator.build_email(
                subject=subject,
                body=message,
                created_by=self.request.user,
                receiving_address=email,
            )
            self.sms_creator.build_sms(
                country_code=country_code,
                phone_number=phone_number,
                body=message,
                created_by=self.request.user,
                patient_obj=patient_obj,
            )
            response_user_ids.append(response_email)
            response_user_ids.append(receiving_address)
        elif any("sms" == item.lower() for item in notification_type):
            self.sms_creator.build_sms(
                country_code=country_code,
                phone_number=phone_number,
                body=message,
                created_by=self.request.user,
                patient_obj=patient_obj,
            )
            response_user_ids.append(receiving_address)
        elif any("email" == item.lower() for item in notification_type):
            response = self.email_creator.build_email(
                subject=subject,
                body=message,
                created_by=self.request.user,
                receiving_address=email,
            )
            response_user_ids.append(response)
        return StandardAPIResponse(
            status=status.HTTP_201_CREATED,
            data={
                "user_ids": response_user_ids,
                "status": "Success",
                # "otp_expiry_seconds": OTP_EXPIRY_IN_SECONDS,
            },
        )

    def post(self, request, *args, **kwargs):
        communication_mode = request.data.get("communication_mode", "None")
        if communication_mode:
            return self.trigger_payment_link(request_data=request.data)
        raise StandardAPIException(
            code="invalid_action",
            detail=ERROR_DETAILS["invalid_action"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PaymentsUpdateRetrieveAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [AllowAny]
    queryset = Payment.objects.all()
    entity = "Payment"
    serializer_class = PaymentSerializer

    def get(self, request, *args, **kwargs):
        raise StandardAPIException(
            code="method_not_allowed",
            detail=ERROR_DETAILS["method_not_allowed"],
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def patch(self, request, *args, **kwargs):
        payment_obj = self.get_object()
        client_payment_status = self.request.data.get("client_payment_status")
        client_payment_response = self.request.data.get("client_payment_response", {})
        if not client_payment_status:
            raise StandardAPIException(
                code="client_payment_status_missing",
                detail=ERROR_DETAILS["client_payment_status_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not client_payment_response:
            raise StandardAPIException(
                code="client_payment_response_missing",
                detail=ERROR_DETAILS["client_payment_response_missing"],
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        txn_id = client_payment_response.get("WidgetArgs", {}).get("TxID")
        transaction_manager = TransactionManager(payment_obj=payment_obj)
        payment_obj, success, message = transaction_manager.update_transaction_status(
            payment_status_from_client=client_payment_status,
            client_payment_response=client_payment_response,
            txn_id=txn_id,
        )
        if not success:
            raise StandardAPIException(
                code=message,
                detail=ERROR_DETAILS.get(message),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentSerializer(payment_obj)
        return StandardAPIResponse(data=serializer.data, status=status.HTTP_200_OK)


class WriteOffListCreateView(StandardListCreateAPIMixin):
    queryset = WriteOff.objects.all()
    serializer_class = WriteOffSerializer
    entity = "Bill"
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    search_fields = ["name"]
    filterset_fields = ["name", "active"]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = filter_by_date_range(
            queryset=queryset,
            valid_from_date=self.request.query_params.get("valid_from"),
            valid_to_date=self.request.query_params.get("valid_to"),
        )
        if self.request.query_params.get("id"):
            queryset = filter_by_id(queryset=self.request.query_params.get("id"))
        return queryset


class WriteOffRetrieveUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = WriteOff.objects.all()
    serializer_class = WriteOffSerializer
    allowed_methods_to_resident = {"get": True}
    entity = "Bill"


class BillPaymentPlanFilter(django_filters.FilterSet):
    service = django_filters.CharFilter(
        lookup_expr="icontains", field_name="bill__service"
    )
    claim_id = django_filters.CharFilter(
        field_name="bill__display_id", lookup_expr="icontains"
    )
    due_date = django_filters.DateFilter(
        field_name="bill__due_date__date", lookup_expr="exact"
    )
    service_date = django_filters.DateFilter(
        field_name="bill__service_date__date", lookup_expr="exact"
    )
    statement_date = django_filters.DateFilter(
        field_name="bill__statement_date__date", lookup_expr="exact"
    )
    patient = django_filters.CharFilter(
        field_name="bill__patient__patient_id", lookup_expr="exact"
    )
    patient_id = django_filters.CharFilter(
        field_name="bill__patient__patient_id", lookup_expr="exact"
    )
    patient_first_name = django_filters.CharFilter(
        field_name="bill__patient__first_name", lookup_expr="icontains"
    )
    patient_last_name = django_filters.CharFilter(
        field_name="bill__patient__last_name", lookup_expr="icontains"
    )
    patient_gender = django_filters.CharFilter(
        field_name="bill__patient__gender", lookup_expr="iexact"
    )
    patient_dob = django_filters.DateFilter(
        field_name="bill__patient__dob", lookup_expr="exact"
    )
    ssn = django_filters.CharFilter(
        field_name="bill__patient__ssn", lookup_expr="exact"
    )
    type_of_service_category = django_filters.CharFilter(
        field_name="bill__breakdown__category__name", lookup_expr="icontains"
    )
    type_of_service_sub_category = django_filters.CharFilter(
        field_name="bill__breakdown__type_of_service__sub_category__name",
        lookup_expr="icontains",
    )
    status = django_filters.CharFilter(method="filter_by_status")
    plan_type = django_filters.CharFilter(
        field_name="payment_plan_id", lookup_expr="exact"
    )
    plan_start_date = django_filters.DateFilter(
        field_name="payment_plan__start_date", lookup_expr="gte"
    )
    plan_end_date = django_filters.DateFilter(
        field_name="payment_plan__end_date", lookup_expr="lte"
    )
    practice_location_id = django_filters.UUIDFilter(
        field_name="bill__practice_location_id", lookup_expr="exact"
    )
    provider_first_name = django_filters.CharFilter(
        field_name="bill__encounter__created_by__first_name", lookup_expr="icontains"
    )
    provider_last_name = django_filters.CharFilter(
        field_name="bill__encounter__created_by__last_name", lookup_expr="icontains"
    )
    service_start_date = django_filters.DateFilter(
        field_name="bill__service_start_date", lookup_expr="exact"
    )
    service_end_date = django_filters.DateFilter(
        field_name="bill__service_end_date", lookup_expr="exact"
    )

    def filter_by_status(self, queryset, name, value):
        values = value.split(",")
        return queryset.filter(status__in=values)

    class Meta:
        model = BillPaymentPlan
        fields = (
            "service",
            "claim_id",
            "due_date",
            "service_date",
            "statement_date",
            "patient",
            "patient_id",
            "patient_first_name",
            "patient_last_name",
            "patient_gender",
            "patient_dob",
            "ssn",
            "type_of_service_category",
            "type_of_service_sub_category",
            "status",
            "plan_type",
            "practice_location_id",
            "provider_first_name",
            "provider_last_name",
            "service_start_date",
            "service_end_date",
        )


class BillPaymentPlanListView(StandardListAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = BillPaymentPlan.objects.for_current_user().order_by("-created_on")
    serializer_class = BillPaymentPlanSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    entity = "BillPaymentPlan"
    search_fields = [
        "name",
        "bill__display_id",
        "bill__patient__first_name",
        "bill__patient__last_name",
        "bill__patient__patient_id",
    ]
    allowed_methods_to_resident = {"get": True}
    filterset_class = BillPaymentPlanFilter


class BillPaymentPlanDetailView(StandardRetieveAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = (
        BillPaymentPlan.objects.for_current_user()
        .select_related("bill", "bill__patient", "bill__encounter", "payment_plan")
        .prefetch_related("bill__payments")
    )
    serializer_class = BillPaymentPlanDetailSerializer
    allowed_methods_to_resident = {"get": True}
    entity = "BillPaymentPlan"


class AdjustmentListCreateView(StandardListCreateAPIMixin):
    queryset = Adjustment.objects.all()
    serializer_class = AdjustmentSerializer
    entity = "Bill"
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = ["name"]
    filterset_fields = ["name", "active"]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = filter_by_date_range(
            queryset=queryset,
            valid_from_date=self.request.query_params.get("valid_from"),
            valid_to_date=self.request.query_params.get("valid_to"),
        )
        if self.request.query_params.get("id"):
            queryset = filter_by_id(
                queryset=queryset, id=self.request.query_params.get("id")
            )
        return queryset


class AdjustmentRetrieveUpdateView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    queryset = Adjustment.objects.all()
    serializer_class = AdjustmentSerializer
    allowed_methods_to_resident = {"get": True}
    entity = "Bill"


class BillRefundRequestsListCreateAPIView(StandardListCreateAPIMixin):
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    permission_classes = [HelixUserBasePermission]
    queryset = BillRefundRequest.objects.all()
    serializer_class = BillRefundRequestSerializer
    filter_class = BillRefundRequestFilter
    # entity = "BillRefundRequest"

    @staticmethod
    def filter_by_bill(queryset, bill):
        return queryset.filter(bill_id=bill)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)

        bill = self.request.query_params.get("bill", None)
        if bill:
            queryset = self.filter_by_bill(queryset=queryset, bill=bill)

        return queryset


class BillRefundRequestRetrieveAPIView(StandardRetrieveUpdateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    queryset = BillRefundRequest.objects.all()
    serializer_class = BillRefundRequestSerializer


class BillCancellationCodeCompositionListCreateAPIView(StandardListCreateAPIMixin):
    permission_classes = [HelixUserBasePermission]
    queryset = BillCancellationCodeComposition.objects.all()
    serializer_class = BillCancellationCodeCompositionSerializer
    filter_class = BillCancellationCodeCompositionFilter


class ServiceCategoryCountView(GenericAPIView):
    permission_classes = [HelixUserBasePermission | IsAuthenticatedResidentPermission]
    allowed_methods_to_resident = {"get": True}

    def get(self, request, *args, **kwargs):
        category = Category.objects.for_current_user().count()
        sub_category = SubCategory.objects.for_current_user().count()
        service = TypeOfService.objects.for_current_user().count()
        required_status_count = {
            "CATEGORIES": category,
            "SUB_CATEGORIES": sub_category,
            "SERVICES": service,
        }
        return StandardAPIResponse(
            data=required_status_count, status=status.HTTP_200_OK
        )
