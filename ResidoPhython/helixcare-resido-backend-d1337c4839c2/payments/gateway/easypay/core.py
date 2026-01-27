import random
import base64
import urllib.parse

from payments.gateway.easypay.configuration import EasyPayConfiguration
from payments.payment_constants import (
    TransactionMethod,
    CARD_BASED_TRANSACTION_METHODS,
    TransactionEvent,
)
from payments.utils import decrypt_data_using_pvt_key
from common.stores.key import key_store
from common.utils.requests import helix_request
from payments.gateway.easypay.constants import (
    AUTHENTICATION,
    CC_SALE,
    ACC_SALE,
    CC_SALE_RECUR,
    CC_CONSENT_CREATE,
    ACC_CONSENT_CREATE,
    CC_CONSENT_PAY,
    ACC_CONSENT_PAY,
    EasyPayTxnStatus,
    APPLY_CREDIT_AKA_REFUND_PATH,
    ACC_VOID_CANCEL_TRANSACTION,
    CARD_VOID_CANCEL_TRANSACTION,
    EasyPayVoidResponseKey,
    EasyPayTransactionType,
    EASY_PAY_TRANSACTION_TYPE_TO_QUERY_TRANSACTION_API_PATH_MAP,
    EASY_PAY_TRANSACTION_TYPE_TO_QUERY_RESPONSE_KEY_MAP,
    EasyPayRefundMethodology,
    RECONCILE_TRANSACTIONS_API_PATH,
)
from payments.models import SavedCard, SavedAccount
from payments.gateway.base import BasePaymentGateway
import requests
from common.utils.logging import logger
import json
import pytz


class EasyPay(BasePaymentGateway):
    def __init__(self, **kwargs):
        super(EasyPay, self).__init__(**kwargs)
        self.rpguid = self.transaction_id or self.bill_id
        self.config = EasyPayConfiguration()
        self.easypay_transaction_type = None

    def set_easypay_transaction_type(self, transaction_method):
        if transaction_method in CARD_BASED_TRANSACTION_METHODS:
            self.easypay_transaction_type = EasyPayTransactionType.CC.value

        if transaction_method == TransactionMethod.BANK_TRANSFER.value:
            self.easypay_transaction_type = EasyPayTransactionType.ACH.value

        return self.easypay_transaction_type

    @property
    def query_transaction_api_path(self):
        return EASY_PAY_TRANSACTION_TYPE_TO_QUERY_TRANSACTION_API_PATH_MAP.get(
            self.easypay_transaction_type
        )

    @property
    def query_transaction_response_key(self):
        return EASY_PAY_TRANSACTION_TYPE_TO_QUERY_RESPONSE_KEY_MAP.get(
            self.easypay_transaction_type
        )

    def process_payment_card(
        self,
        amount: float,
        card: SavedCard,
        cvv: str,
        payment_term: int,
        installment_date,
    ) -> dict:
        return self._process_payment_card(
            amount, card, cvv, payment_term, installment_date
        )

    def process_payment_account(self, amount: float, account: SavedAccount) -> dict:
        return self._process_payment_account(amount, account)

    def cancel_payment(self, txn_id: any, payment_method) -> dict:
        status, error_message = self.get_transaction_status(
            payment_id=None, txn_id=txn_id, transaction_method=payment_method
        )
        if status == EasyPayTxnStatus.OPEN.value:
            return self._cancel_payment(
                transaction_id=txn_id, payment_method=payment_method
            )
        else:
            return {
                "status": False,
                "message": f"Payment transaction_id {txn_id} cannot be cancelled and current status is {status}",
                "error": error_message,
                "response_data": None,
            }

    def _authenticate(self) -> str:
        url = f"{self.config.base_url}{AUTHENTICATION}"
        payload = {"AcctCode": self.config.acc_code, "Token": self.config.token}
        headers = {"Content-Type": "application/json"}
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            resp = response.json()
            return resp["AuthenticateResult"]["SessKey"]
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Authentication error: {req_err}")
            raise RuntimeError(f"Authentication failed: {req_err}")

    def _process_payment_card(
        self,
        amount: float,
        card: SavedCard,
        cvv: str,
        payment_term: int,
        installment_date,
    ) -> dict:
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        if payment_term is not None and payment_term > 0:
            payload = self._construct_payload_recur(
                amount, card, cvv, payment_term, installment_date
            )
            return self._process_payment_card_recur(payload, headers)
        else:
            payload = self._construct_payload_card(amount, card, cvv)
            return self._process_payment_card_full(payload, headers)

    @staticmethod
    def _get_cancellation_path_and_response_key(payment_method):
        cancellation_path, response_key = (
            CARD_VOID_CANCEL_TRANSACTION,
            EasyPayVoidResponseKey.CARD_VOID_RESPONSE_KEY.value,
        )
        if payment_method == TransactionMethod.BANK_TRANSFER.value:
            cancellation_path, response_key = (
                ACC_VOID_CANCEL_TRANSACTION,
                EasyPayVoidResponseKey.ACC_VOID_RESPONSE_KEY.value,
            )

        return cancellation_path, response_key

    def _cancel_payment(self, transaction_id, payment_method) -> dict:
        """
        Cancels a payment transaction using EasyPay Void API.
        """
        cancellation_path, response_key = self._get_cancellation_path_and_response_key(
            payment_method=payment_method
        )
        url = f"{self.config.base_url}{cancellation_path}"

        try:
            if isinstance(transaction_id, str):
                if transaction_id.startswith("MOCK"):
                    return {
                        "success": True,
                        "message": "Transaction has been successfully mock cancelled",
                        "ErrCode": None,
                        "error": None,
                        "response_data": None,
                    }
                transaction_id = int(transaction_id)

            payload = {"TxID": transaction_id}
            session_key = self._authenticate()
            headers = self._get_headers(session_key)
            response, call_log = helix_request.post(
                url=url, headers=headers, json=payload
            )
            self.transaction_obj.log(
                event=TransactionEvent.VOID_GATEWAY.value,
                data=call_log.get("Response", {}).get("response_body"),
                call_log=call_log,
            )
            response.raise_for_status()
            response_data = response.json()

            if response_data.get(response_key, {}).get("TxApproved"):
                return {
                    "success": True,
                    "message": "Transaction has been successfully cancelled.",
                    "ErrCode": None,
                    "error": None,
                    "response_data": response_data,
                }
            else:
                err_code = response_data.get(response_key, {}).get("ErrCode", "Unknown")
                err_msg = response_data.get(response_key, {}).get(
                    "ErrMsg", "Unknown error"
                )

                logger.error(
                    f"Cancellation failed for transaction_id {transaction_id} and ErrCode: {err_code}, Error: {err_msg}"
                )
                return {
                    "success": False,
                    "message": "Failed to cancel the transaction",
                    "ErrCode": err_code,
                    "error": err_msg,
                    "response_data": response_data,
                }

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Cancellation error: {req_err}")
            return {
                "success": False,
                "ErrCode": "Cancellation error",
                "message": "Failed to cancel the transaction",
                "error": str(req_err),
                "response_data": None,
            }

    def _process_payment_card_full(self, payload, headers) -> dict:
        url = f"{self.config.base_url}{CC_SALE}"
        response_data, transaction_id = None, None
        try:
            response, call_log = helix_request.post(
                url=url, headers=headers, json=payload
            )
            self.transaction_obj.log(
                event=TransactionEvent.SALE_GATEWAY.value,
                data=call_log.get("Response", {}).get("response_body"),
                call_log=call_log,
            )
            response.raise_for_status()
            response_data = response.json()
            transaction_id = response_data.get("CreditCardSale_ManualResult", {}).get(
                "TxID"
            )
            if (
                response_data["CreditCardSale_ManualResult"]["FunctionOk"]
                and response_data["CreditCardSale_ManualResult"]["TxApproved"]
            ):
                return {
                    "success": True,
                    "data": response_data,
                    "transaction_id": transaction_id,
                }
            else:
                err_code = response_data["CreditCardSale_ManualResult"]["ErrCode"]
                err_msg = response_data["CreditCardSale_ManualResult"][
                    "ErrMsg"
                ] or response_data.get("CreditCardSale_ManualResult", {}).get(
                    "RespMsg", ""
                )

                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "ErrCode": err_code,
                    "error": err_msg,
                    "data": response_data,
                    "transaction_id": transaction_id,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "error": "Payment error",
                "details": str(req_err),
                "data": response_data,
                "transaction_id": transaction_id,
            }

    def charge_cc_using_consent(self, consent_id, amount):
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = {
            "ConsentID": consent_id,
            "ProcessAmount": amount,
        }
        url = f"{self.config.base_url}{CC_CONSENT_PAY}"
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get(
                "ConsentAnnual_ProcPaymentResult"
            ) and response_data.get("ConsentAnnual_ProcPaymentResult").get(
                "TxApproved"
            ):
                return {
                    "success": True,
                    "data": response_data.get("ConsentAnnual_ProcPaymentResult"),
                }
            else:
                err_code = response_data["ConsentAnnual_ProcPaymentResult"]["ErrCode"]
                err_msg = response_data["ConsentAnnual_ProcPaymentResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "message": "Error Processing Consent",
                    "error_code": err_code,
                    "error": err_msg,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "message": "Error Processing Consent",
                "error": str(req_err),
                "error_code": None,
            }

    def charge_acc_using_consent(self, consent_id, amount):
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = {
            "ConsentID": consent_id,
            "ProcessAmount": amount,
        }
        url = f"{self.config.base_url}{ACC_CONSENT_PAY}"
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get(
                "ACHConsentAnnual_ProcPaymentResult"
            ) and response_data.get("ACHConsentAnnual_ProcPaymentResult").get(
                "TxApproved"
            ):
                return {
                    "success": True,
                    "data": response_data.get("ACHConsentAnnual_ProcPaymentResult"),
                }
            else:
                err_code = response_data["ACHConsentAnnual_ProcPaymentResult"][
                    "ErrCode"
                ]
                err_msg = response_data["ACHConsentAnnual_ProcPaymentResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "message": "Error Processing Consent",
                    "error_code": err_code,
                    "error": err_msg,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "message": "Error Processing Consent",
                "error": str(req_err),
                "error_code": None,
            }

    def create_consent_on_account(self, account: SavedAccount) -> dict:
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = self._construct_acc_consent_payload(account=account)
        url = f"{self.config.base_url}{ACC_CONSENT_CREATE}"
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if (
                response_data.get("ACHTransaction_ComboResult")
                and response_data.get("ACHTransaction_ComboResult").get("ConsentID")
                is not None
            ):
                return {
                    "success": True,
                    "data": response_data.get("ACHTransaction_ComboResult"),
                }
            else:
                err_code = response_data["ACHTransaction_ComboResult"]["ErrCode"]
                err_msg = response_data["ACHTransaction_ComboResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "message": "Error Processing Consent",
                    "error_code": err_code,
                    "error": err_msg,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "message": "Error Processing Consent",
                "error": str(req_err),
                "error_code": None,
            }

    def _construct_acc_consent_payload(
        self,
        account: SavedAccount,
    ):
        account_holder_data = self._get_account_holder_data(
            account.patient,
            account.billing_address_1,
            account.billing_address_2,
            account.billing_city,
            account.billing_state,
            account.billing_zip,
            account.billing_country,
            account.first_name,
            account.last_name,
        )
        return {
            "ChargeDetails": {
                "AccountNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(account.account_number),
                        key_store.tn_auth_private_key,
                    )
                    if account.data_encrypted
                    else account.account_number
                ),
                "RoutingNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(account.routing_number),
                        key_store.tn_auth_private_key,
                    )
                    if account.data_encrypted
                    else account.routing_number
                ),
                "Amount": 0,
                "AccountType": account.account_type,
            },
            "AcctHolder": account_holder_data,
            "EndCustomer": self._get_end_customer_data(),
            "PurchItems": {
                "ServiceDescrip": "",
                "ClientRefID": str(self.bill.id),
                "RPGUID": str(self.bill.id),
            },
            "MerchID": 1,
        }

    def create_consent_on_card(
        self,
        full_amount: float,
        emi_amount: float,
        consent_days: int,
        start_date,
        card: SavedCard,
        cvv: str,
    ) -> dict:
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = self._construct_cc_consent_payload(
            full_amount=full_amount,
            emi_amount=emi_amount,
            consent_days=consent_days,
            card=card,
            start_date=start_date,
            cvv=cvv,
        )
        url = f"{self.config.base_url}{CC_CONSENT_CREATE}"
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if response_data.get(
                "ConsentAnnual_Create_MANResult"
            ) and response_data.get("ConsentAnnual_Create_MANResult").get(
                "CreationSuccess"
            ):
                return {
                    "success": True,
                    "data": response_data.get("ConsentAnnual_Create_MANResult"),
                }
            else:
                err_code = response_data["ConsentAnnual_Create_MANResult"]["ErrCode"]
                err_msg = response_data["ConsentAnnual_Create_MANResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "message": "Error Processing Consent",
                    "error_code": err_code,
                    "error": err_msg,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "message": "Error Processing Consent",
                "error": str(req_err),
                "error_code": None,
            }

    def _process_payment_card_recur(self, payload, headers) -> dict:
        url = f"{self.config.base_url}{CC_SALE_RECUR}"
        try:
            response, _ = helix_request.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if (
                response_data["ConsentRecurring_CreateResult"]["FunctionOk"]
                and response_data["ConsentRecurring_CreateResult"]["CreationSuccess"]
            ):
                return {"success": True, "data": response_data}
            else:
                err_code = response_data["ConsentRecurring_CreateResult"]["ErrCode"]
                err_msg = response_data["ConsentRecurring_CreateResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "ErrCode": err_code,
                    "error": err_msg,
                    "data": response_data,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "error": "Payment error",
                "details": str(req_err),
                "data": None,
            }

    def _process_payment_account(self, amount: float, account: SavedAccount) -> dict:
        url = f"{self.config.base_url}{ACC_SALE}"
        payload = self._construct_payload_acc(amount, account)
        session_key = self._authenticate()
        headers = self._get_headers(session_key)

        response_data, transaction_id = None, None
        try:
            response, call_log = helix_request.post(
                url=url, headers=headers, json=payload
            )
            self.transaction_obj.log(
                event=TransactionEvent.SALE_GATEWAY.value,
                data=call_log.get("Response", {}).get("response_body"),
                call_log=call_log,
            )
            response.raise_for_status()
            response_data = response.json()
            transaction_id = response_data.get("ACHTransaction_SaleResult", {}).get(
                "TxID"
            )
            if (
                response_data["ACHTransaction_SaleResult"]["FunctionOk"]
                and response_data["ACHTransaction_SaleResult"]["TxApproved"]
            ):
                return {
                    "success": True,
                    "data": response_data,
                    "transaction_id": transaction_id,
                }
            else:
                err_code = response_data["ACHTransaction_SaleResult"]["ErrCode"]
                err_msg = response_data["ACHTransaction_SaleResult"]["ErrMsg"]
                logger.error(
                    f"Payment failed with ErrCode: {err_code}, error: {err_msg}"
                )
                return {
                    "success": False,
                    "ErrCode": err_code,
                    "error": err_msg,
                    "data": response_data,
                    "transaction_id": transaction_id,
                }
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Payment error: {req_err}")
            return {
                "success": False,
                "error": "Payment error",
                "details": str(req_err),
                "data": response_data,
                "transaction_id": transaction_id,
            }

    def _construct_payload_card(self, amount: float, card: SavedCard, cvv: str) -> dict:
        account_holder_data = self._get_account_holder_data(
            card.patient,
            card.billing_address_1,
            card.billing_address_2,
            card.billing_city,
            card.billing_state,
            card.billing_zip,
            card.billing_country,
            card.first_name,
            card.last_name,
        )

        return {
            "ccCardInfo": {
                "AccountNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(card.card_number),
                        key_store.tn_auth_private_key,
                    )
                    if card.data_encrypted
                    else card.card_number
                ),
                "ExpMonth": card.expiration_month,
                "ExpYear": card.expiration_year,
                "CSV": cvv,
            },
            "AcctHolder": account_holder_data,
            "EndCustomer": self._get_end_customer_data(),
            "Amounts": self._construct_amounts(amount),
            "PurchItems": {
                "ServiceDescrip": "HelixBeat",
                "ClientRefID": "",
                "RPGUID": self.transaction_id,
            },
            "MerchID": 1,
        }

    def _construct_payload_acc(self, amount: float, account: SavedAccount) -> dict:
        account_holder_data = self._get_account_holder_data(
            account.patient,
            account.billing_address_1,
            account.billing_address_2,
            account.billing_city,
            account.billing_state,
            account.billing_zip,
            account.billing_country,
        )

        return {
            "ChargeDetails": {
                "AccountNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(account.account_number),
                        key_store.tn_auth_private_key,
                    )
                    if account.data_encrypted
                    else account.account_number
                ),
                "RoutingNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(account.routing_number),
                        key_store.tn_auth_private_key,
                    )
                    if account.data_encrypted
                    else account.routing_number
                ),
                "Amount": float(amount.amount),
                "AccountType": account.account_type,
            },
            "AcctHolder": account_holder_data,
            "EndCustomer": self._get_end_customer_data(),
            "PurchItems": {
                "ServiceDescrip": "HelixBeat",
                "ClientRefID": "",
                "RPGUID": self.rpguid,
            },
            "MerchID": 1,
        }

    def _construct_payload_recur(
        self,
        amount: float,
        card: SavedCard,
        cvv: str,
        payment_term: int,
        installment_date,
    ) -> dict:
        account_holder_data = self._get_account_holder_data(
            card.patient,
            card.billing_address_1,
            card.billing_address_2,
            card.billing_city,
            card.billing_state,
            card.billing_zip,
            card.billing_country,
        )

        return {
            "ccCardInfo": {
                "AccountNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(card.card_number),
                        key_store.tn_auth_private_key,
                    )
                    if card.data_encrypted
                    else card.card_number
                ),
                "ExpMonth": card.expiration_month,
                "ExpYear": card.expiration_year,
                "CSV": cvv,
                "Track": "%B4788250000028291^VISA TEST/GOOD^231010100733000000?;4895390000000013=151210100000733?",
            },
            "ConsentCreator": {
                "MerchID": 1,
                "CustomerRefID": str(card.patient.patient_id) + str(self.bill.id),
                "ServiceDescrip": "",
                "RPGUID": self.rpguid,
                "StartDate": self._to_ms_datetime(installment_date),
                "NumPayments": payment_term,
                "TotalAmount": float(amount.amount),
                "Period": 2,
            },
            "AcctHolder": account_holder_data,
            "EndCustomer": self._get_end_customer_data(),
        }

    def _construct_cc_consent_payload(
        self,
        full_amount: float,
        emi_amount: float,
        consent_days: int,
        start_date,
        card: SavedCard,
        cvv: str,
    ) -> dict:
        account_holder_data = self._get_account_holder_data(
            card.patient,
            card.billing_address_1,
            card.billing_address_2,
            card.billing_city,
            card.billing_state,
            card.billing_zip,
            card.billing_country,
        )

        return {
            "ccCardInfo": {
                "AccountNumber": (
                    decrypt_data_using_pvt_key(
                        base64.b64decode(card.card_number),
                        key_store.tn_auth_private_key,
                    )
                    if card.data_encrypted
                    else card.card_number
                ),
                "ExpMonth": card.expiration_month,
                "ExpYear": card.expiration_year,
                "CSV": cvv,
            },
            "ConsentCreator": {
                "MerchID": 1,
                "CustomerRefID": str(card.patient.patient_id) + str(self.bill.id),
                "ServiceDescrip": "",
                "RPGUID": str(self.bill.id),
                "StartDate": self._to_ms_datetime(start_date),
                "NumDays": consent_days,
                "LimitLifeTime": full_amount,
                "LimitPerCharge": emi_amount,
            },
            "AcctHolder": account_holder_data,
            "EndCustomer": self._get_end_customer_data(),
        }

    @staticmethod
    def _construct_amounts(amount: float) -> dict:
        return {
            "TotalAmt": float(amount.amount),
            "SalesTax": 0,
            "Surcharge": 0,
            "Tip": 0,
            "CashBack": 0,
            "ClinicAmount": 0,
            "VisionAmount": 0,
            "PrescriptionAmount": 0,
            "DentalAmount": 0,
            "TotalMedicalAmount": 0,
        }

    @staticmethod
    def _get_account_holder_data(
        patient,
        address1,
        address2,
        city,
        state,
        zip_code,
        country,
        first_name=None,
        last_name=None,
    ) -> dict:
        return {
            "Firstname": first_name or patient.first_name,
            "Lastname": last_name or patient.last_name,
            "Company": "",
            "Title": "",
            "Url": "",
            "BillIngAdress": {
                "Address1": address1,
                "Address2": address2,
                "City": city,
                "State": state,
                "ZIP": zip_code,
                "Country": country,
            },
            "Email": patient.email,
            "Phone": patient.phone_number,
        }

    @staticmethod
    def _get_end_customer_data() -> dict:
        return {
            "Firstname": "",
            "Lastname": "",
            "Company": "",
            "Title": "",
            "Url": "",
            "BillIngAdress": {
                "Address1": "",
                "Address2": "",
                "City": "",
                "State": "",
                "ZIP": "",
                "Country": "",
            },
            "Email": "",
            "Phone": "",
        }

    @staticmethod
    def _get_headers(session_key: str) -> dict:
        return {"Content-Type": "application/json", "SessKey": session_key}

    @staticmethod
    def _to_ms_datetime(dt):
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        timestamp_ms = int(dt.timestamp() * 1000)
        offset = dt.strftime("%z")
        microsoft_json_date = f"/Date({timestamp_ms}{offset})/"
        return microsoft_json_date

    @staticmethod
    def get_account_holder_data_for_pos_payment(patient_obj):
        _data = {
            "Firstname": patient_obj.user.first_name,
            "Lastname": patient_obj.user.last_name,
            "address": {
                "Address1": patient_obj.address,
                "Address2": patient_obj.address_1,
                "City": patient_obj.city,
                "State": patient_obj.state,
                "ZIP": patient_obj.zipcode,
                "Country": patient_obj.country,
            },
            "Phone": patient_obj.user.phone,
        }
        json_data = json.dumps(_data)
        return urllib.parse.quote_plus(json_data)

    @staticmethod
    def get_purchase_details_for_pos_payment(payment_obj):
        _data = {
            "REFID": str(payment_obj.id),
            "RPGUID": str(payment_obj.id),  # This should be payment id
            "ServiceDesc": payment_obj.bill.service,
        }
        json_data = json.dumps(_data)
        return urllib.parse.quote_plus(json_data)

    @staticmethod
    def get_amount_json(amount):
        _data = {
            "baseAmt": str(amount),
            "feeAmt": "0.00",
            "totalAmt": str(amount),
        }
        json_data = json.dumps(_data)
        return urllib.parse.quote_plus(json_data)

    def prepare_request_for_pos_payment(self, payment_obj, amount):
        logger.info("Preparing Request For Pos Payment")
        session_key = self._authenticate()
        account_holder_data = self.get_account_holder_data_for_pos_payment(
            patient_obj=payment_obj.bill.patient
        )
        purchase_details = self.get_purchase_details_for_pos_payment(
            payment_obj=payment_obj
        )
        amount_json = self.get_amount_json(amount=amount)

        return {
            "message": "POS Payment request prepared",
            "SessKey": session_key,
            "AcctHolderJson": account_holder_data,
            "EndCustJson": account_holder_data,
            "PurchDetailsJson": purchase_details,
            "Amount": amount_json,
            "SaveCard": False,
        }

    @staticmethod
    def get_mock_transaction_data():
        return {
            "ACCT_FIRST_NAME": "Sean",
            "ACCT_LAST_NAME": "Wood",
            "ACCT_NO": "4788XXXXXXXX8291",
            "AMOUNT": 10,
            "AVSr": "Y",
            "AcctHolderID": 3,
            "BatchLogID": 0,
            "BatchNO": 0,
            "BatchStatus": "N",
            "CARD_TYPE": "VI",
            "CASHBACK": 0,
            "CVVr": "",
            "CardPresent": True,
            "ConsentID": 0,
            "CreatedOn": "/Date(1549947600000-0500)/",
            "Credits": 0,
            "EMVPresent": True,
            "EMVRecTags": "",
            "EXP_DATE": "1028",
            "EndCustID": 44,
            "Flags": "",
            "HAuthorizedAmount": -1,
            "ID": 44,
            "IsLocked": False,
            "IsPartialApproval": False,
            "LAST_CHANGED_BY": "vidya_Venkatraman",
            "LastChangedOn": "/Date(1549947600000-0500)/",
            "MerchID": 1,
            "Origin": "API",
            "PAYMENT_TYPE": "C",
            "PartialAuthApproved": -1,
            "PreAuthID": 0,
            "PrepaidBalance": -1,
            "REF_ID": "A97689#",
            "RPGUID": "adf98580-b4ab-42fc-bb99-01c89964afe9",
            "RefTxID": 0,
            "SALE_TAX": 0,
            "SEQ_NO": 51,
            "SERVER": "",
            "SURCHARGE": 0,
            "TIP": 0,
            "TXN_CODE": "092682",
            "TXN_DATE": "042419",
            "TXN_DATETIME": "/Date(1549947600000-0500)/",
            "TXN_TIME": "082544",
            "TxLOCK": "7A639CD720CE4B14",
            # TODO For increasing the probability of success txns, increased the count. 9/10 is the success probability
            "TxSTATUS": random.choice(
                [
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.OPEN.value,
                    EasyPayTxnStatus.FAILED.value,
                ]
            ),
            "TxType": "CCSALE",
            "UserID": 2547,
        }

    def get_transaction_data(self, query_response_data):
        query_results = query_response_data.get(self.query_transaction_response_key, {})
        error_message = query_results.get("ErrMsg")
        if error_message:
            return None, f"gateway_error: {error_message}"

        transactions = query_results.get("Transactions", [{}])
        if transactions:
            return transactions[0], None

        return None, "no_transaction_found"

    def query_transaction(self, txn_id, transaction_method, payment_id=None):
        """
            method to search a transaction in EasyPay

            N='{payment_id}'    While searching with RPGUID
            H=txn_id            While searching with txn_id

        :param payment_id:
        :param transaction_method:
        :param txn_id:
        :return:
        """
        if txn_id.startswith("MOCK"):
            return self.get_mock_transaction_data(), None

        self.easypay_transaction_type = self.set_easypay_transaction_type(
            transaction_method=transaction_method
        )
        if not self.easypay_transaction_type:
            return None, {
                "code": "invalid_transaction_method",
                "message": f"Invalid transaction method - {transaction_method}",
            }

        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = {"Query": f"(H={int(txn_id)})"}  # H Stands for transaction id
        if payment_id:
            payload = {"Query": f"(N='{str(payment_id)}')"}  # N stands for RPGUID
        url = f"{self.config.base_url}{self.query_transaction_api_path}"

        response, call_log = helix_request.post(url=url, headers=headers, json=payload)
        self.transaction_obj.log(
            event=TransactionEvent.QUERY_GATEWAY.value,
            data=call_log.get("Response", {}).get("response_body"),
            call_log=call_log,
        )
        if response is not None and response.status_code == 200:
            query_response_data = response.json()

            return self.get_transaction_data(query_response_data=query_response_data)

        return None, {
            "code": "unknown_error",
            "message": f"Unknown Error Occurred - {call_log.get('Response', {}).get('exception')}",
        }

    def get_transaction_status(self, payment_id, txn_id, transaction_method):
        transaction_data, error_message = self.query_transaction(
            payment_id=payment_id, txn_id=txn_id, transaction_method=transaction_method
        )
        if error_message or not transaction_data:
            return None, error_message

        return transaction_data.get("TxSTATUS"), error_message

    @staticmethod
    def _get_mock_refund_details():
        refund_response_data = {
            "Transaction_ApplyCreditResult": {
                "ErrCode": 0,
                "ErrMsg": "",
                "FunctionOk": True,
                "RespMsg": "Success credit Pending Transaction ID: MOCK-0000057",
                "TxApproved": True,
                "TxID": "MOCK-57",
            }
        }
        return True, refund_response_data

    @staticmethod
    def _get_refund_details_from_call_log(call_log):
        response_status_code = call_log.get("Response", {}).get("status_code")
        response_body = call_log.get("Response", {}).get("response_body", {})
        if response_status_code != 200:
            return False, response_body

        refund_status = response_body.get("Transaction_ApplyCreditResult", {}).get(
            "TxApproved"
        )
        return bool(refund_status), response_body

    def _refund_transaction(self, txn_id, amount):
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = {"TxID": int(txn_id), "CreditAmount": amount}
        url = f"{self.config.base_url}{APPLY_CREDIT_AKA_REFUND_PATH}"
        response, call_log = helix_request.post(url=url, headers=headers, json=payload)
        self.transaction_obj.log(
            event=TransactionEvent.CREDIT_GATEWAY.value,
            data=call_log.get("Response", {}).get("response_body"),
            call_log=call_log,
        )

        if txn_id.startswith("MOCK"):
            return self._get_mock_refund_details()

        return self._get_refund_details_from_call_log(call_log=call_log)

    def refund_transaction(self, parent_id, txn_id, amount, payment_method):
        """

        :param parent_id:
        :param txn_id:
        :param amount:
        :param payment_method:
        :return:
        """
        # TODO MUST how to handle other status from EasyPay like FAILED
        if txn_id is None:
            logger.info(
                f"Transaction ID received None while processing refund txn {self.transaction_id}"
            )
            return False, {"error": f"null_txn_id for {parent_id}"}, None

        current_status, error_message = self.get_transaction_status(
            payment_id=None, txn_id=txn_id, transaction_method=payment_method
        )
        if not current_status:
            logger.info(
                f"Cannot refund transaction with payment_id {parent_id} and txn_id {txn_id} - {error_message}"
            )
            return False, error_message, None

        if current_status == EasyPayTxnStatus.SETTLED.value:
            refund_status, response_body = self._refund_transaction(
                txn_id=txn_id, amount=amount
            )
            return (
                refund_status,
                response_body,
                EasyPayRefundMethodology.APPLY_CREDIT.value,
            )

        if current_status == EasyPayTxnStatus.OPEN.value:
            cancel_response_dict = self._cancel_payment(
                transaction_id=txn_id, payment_method=payment_method
            )
            return (
                cancel_response_dict.get("success"),
                cancel_response_dict.get("response_data"),
                EasyPayRefundMethodology.VOID.value,
            )

        if current_status == EasyPayTxnStatus.FAILED.value:
            return False, "txn_failed_at_gateway", None

    def _reconcile_transactions(self, **kwargs):
        start_date_str = kwargs.get("start_date")
        end_date_str = kwargs.get("end_date")
        query_type = kwargs.get("query_type")
        session_key = self._authenticate()
        headers = self._get_headers(session_key)
        payload = {
            "StartDate": start_date_str,
            "EndDate": end_date_str,
            "qType": query_type,
        }
        url = f"{self.config.base_url}{RECONCILE_TRANSACTIONS_API_PATH}"
        response, call_log = helix_request.post(url=url, headers=headers, json=payload)

        response_status_code = call_log.get("Response", {}).get("status_code")
        response_body = call_log.get("Response", {}).get("response_body", {})
        if response_status_code != 200:
            return False, response_body

        return True, response_body

    def reconcile_transactions(self, **kwargs):
        logger.info(f"Reconciling transactions from easypay for - {kwargs}")
        success, response_data = self._reconcile_transactions(**kwargs)
        reconcile_results = response_data.get("ReconcileResult", {})
        error_code, error_message, transactions = (
            reconcile_results.get("ErrCode"),
            reconcile_results.get("ErrMsg"),
            reconcile_results.get("Transactions", []),
        )
        if success and error_message:
            success = False
        logger.error(
            f"Transaction Reconciliation result for {kwargs} - "
            f"{success}, {error_code}, {error_message}, {len(transactions)}"
        )
        return success, transactions, error_code, error_message
