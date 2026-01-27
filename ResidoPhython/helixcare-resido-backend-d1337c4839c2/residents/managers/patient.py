import string
import time
import random

from django.db import connection
from django.db.models import Q

from common.managers.model.base import BaseModelManager
from residents.models import Resident
from helixauth.token.resident.access import ResidentAccessToken
from helixauth.utils import create_verification_code
from .patientfamily import PatientFamilyManager
from ..constants import (
    TransactionType,
    RESIDENT_INVITATION_EMAIL_BODY,
    RESIDENT_INVITATION_EMAIL_SUBJECT,
    RESIDENT_INVITATION_FORM_URL,
    RESIDENT_INVITATION_LINK_EXPIRY,
)
from notifications.managers.notification import NotificationsManager
import os
from django.template import Template, Context


class ResidentManager(BaseModelManager):
    model = Resident

    PATIENT_INPUT_DATA_ATTRS = [
        "dob",
        "zipcode",
        "city",
        "state",
        "country",
        "first_name",
        "last_name",
        "gender",
    ]
    FAMILY_INPUT_DATA_ATTRS = ["dob", "first_name", "last_name", "gender"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patient_obj = kwargs.get("patient_obj")
        self.patient_uuid = kwargs.get("patient_uuid")
        self.patient_data = kwargs.get("patient_data", {})

    @classmethod
    def get_resident(cls, patient_id):
        return cls.filter_by(id=patient_id).first()

    @classmethod
    def is_resident_with_email_phone_number_exists(cls, email, phone_number):
        if not email and not phone_number:
            return False

        queries = Q()
        if email:
            queries = Q(email__iexact=email)
        if phone_number:
            queries = queries | Q(phone_number=phone_number)
        try:
            cls.model.objects.get(queries)
            return True
        except cls.model.DoesNotExist:
            return False

    @classmethod
    def get_full_resident(
        cls,
        email,
        phone_number,
        first_name=None,
        last_name=None,
        dob=None,
        zipcode=None,
    ):
        if not email and not phone_number:
            return None

        queries = Q()
        if email:
            queries = Q(email__iexact=email)
        if phone_number:
            queries = queries | Q(phone_number=phone_number)
        if dob:
            queries = queries & Q(dob=dob)
        if zipcode:
            queries = queries & Q(zipcode=zipcode)
        if first_name:
            queries = queries & Q(first_name__iexact=first_name)
        if last_name:
            queries = queries & Q(last_name__iexact=last_name)
        queries = queries & Q(is_guest_patient=False)

        return cls.model.objects.filter(queries).first()

    @classmethod
    def get_guest_patient(cls, email, phone_number, dob=None, zipcode=None):
        if not email and not phone_number:
            return None

        is_guest_patient_query = Q(is_guest_patient=True)
        queries = is_guest_patient_query
        search_query = Q()
        if email:
            search_query = search_query | Q(email__iexact=email)
        if phone_number:
            search_query = search_query | Q(phone_number=phone_number)

        if dob:
            search_query = search_query & Q(dob=dob)
        if zipcode:
            search_query = search_query & Q(zipcode=zipcode)

        if len(search_query) > 0:
            queries = is_guest_patient_query & search_query

        guest_patient = cls.model.objects.filter(queries).first()
        return guest_patient

    @staticmethod
    def check_patient_exists_and_matches(patient_data):
        email, phone_number = patient_data.get("email"), patient_data.get(
            "phone_number"
        )
        queries = Q()
        if email:
            queries = Q(email__iexact=email)
        if phone_number:
            queries = queries | Q(phone_number=phone_number)

        patient = Resident.objects.filter(queries).first()

        if not patient:
            return patient, False

        (
            fname_in_request,
            lname_in_request,
            dob_in_request,
            gender_in_request,
            zipcode_in_request,
        ) = (
            patient_data.get("first_name"),
            patient_data.get("last_name"),
            patient_data.get("dob"),
            patient_data.get("gender"),
            patient_data.get("zipcode"),
        )

        matching = (
            patient.first_name == fname_in_request
            and patient.last_name == lname_in_request
            and patient.gender == gender_in_request
            and patient.zipcode == zipcode_in_request
            and patient.dob == dob_in_request
        )

        return patient, matching

    @classmethod
    def check_patient_existence(
        cls, patient_data, booker_patient=None, booker_relationship=None
    ):
        if booker_patient:
            queryset = PatientFamilyManager.get_patient_family_relations(booker_patient)
        else:
            email = patient_data.get("email", None)
            phone_number = patient_data.get("phone_number", None)
            if not email and not phone_number:
                return False, None
            queries = Q()
            if email:
                queries = queries | Q(email__iexact=email)
            if phone_number:
                queries = queries | Q(phone_number=phone_number)
            queryset = cls.model.objects.filter(queries).order_by("created_on")
        if not queryset.exists():
            return False, None
        for record in queryset.iterator():
            if booker_patient:
                family = record.family
                matched_attrs = cls.get_matched_attrs_patient_with_input_data(
                    family, patient_data, cls.FAMILY_INPUT_DATA_ATTRS
                )
                if (str(record.relationship).lower()) == str(
                    booker_relationship
                ).lower():
                    matched_attrs += 1
                # if all matches, then return this
                if matched_attrs == 5:
                    return True, family
            else:
                existed_patient = record
                matched_attrs = cls.get_matched_attrs_patient_with_input_data(
                    existed_patient, patient_data, cls.PATIENT_INPUT_DATA_ATTRS
                )
                if matched_attrs > 5:
                    return True, existed_patient
        if booker_patient:
            return False, None
        return True, None

    @staticmethod
    def get_matched_attrs_patient_with_input_data(existed_patient, patient_data, attrs):
        matched_attrs = 0
        for attr in attrs:
            if str(getattr(existed_patient, attr)) == str(patient_data.get(attr, None)):
                matched_attrs += 1
        return matched_attrs

    @classmethod
    def create_patient_family_relation(cls, patient, family, relationship):
        return PatientFamilyManager.model.objects.get_or_create(
            patient=patient, member=family, defaults={"relationship": relationship}
        )

    @classmethod
    def get_resident_id_suffix(cls):
        return int(time.time())

    @classmethod
    def get_resident_id_prefix(cls, first_name, last_name):
        return f"{first_name[:3]}{last_name[:3]}"

    @classmethod
    def get_unique_resident_id_string(cls, length=6):
        characters = string.digits
        username = "".join(random.choice(characters) for _ in range(length))
        return username

    @classmethod
    def generate_resident_id(cls, first_name, last_name):
        prefix = cls.get_resident_id_prefix(first_name=first_name, last_name=last_name)
        unique_element = cls.get_unique_resident_id_string()
        # suffix = cls.get_patient_id_suffix()

        resident_id = f"{prefix}{unique_element}"
        return resident_id.upper()

    @classmethod
    def get_resident_by_auth_user_id(cls, auth_user_id):
        return Resident.objects.filter(user__auth_user_id=auth_user_id).first()

    def _update_wallet_balance(
        self, amount, transaction_type=TransactionType.CREDIT.value
    ):
        if transaction_type == TransactionType.CREDIT.value:
            self.patient_obj.wallet_balance += amount
            self.patient_obj.save()
            return self.patient_obj

        if transaction_type == TransactionType.DEBIT.value:
            self.patient_obj.wallet_balance -= amount
            self.patient_obj.save()
            return self.patient_obj

        return None

    def credit_wallet_balance(self, amount):
        return self._update_wallet_balance(
            amount=amount, transaction_type=TransactionType.CREDIT.value
        )

    @staticmethod
    def _get_token(instance):
        reset_password_token_expiry = int(time.time()) + RESIDENT_INVITATION_LINK_EXPIRY

        common_token_identity = {
            "tenant": connection.tenant,
            "expiry": reset_password_token_expiry,
            "sub_token_type": "rental_request_form",
        }

        token = ResidentAccessToken.for_tenant_resident(
            resident=instance, **common_token_identity
        )

        return str(token)

    @staticmethod
    def send_email(instance):
        mngr = NotificationsManager(user=instance)
        domain = connection.tenant.domain
        tanant_name = connection.tenant.name
        _token = ResidentManager._get_token(instance)
        code = create_verification_code(
            user_id=str(instance.user.id), user_type=2, channel="EMAIL"
        )
        url = RESIDENT_INVITATION_FORM_URL.format(
            domain=domain,
            user_id=str(instance.user.id),
            # token=token,
            code=code,
            user_type=2,
        )

        # Load and render HTML template
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "notifications",
            "templates",
            "email",
            "resident_invitation.html",
        )

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            template = Template(template_content)
            context = Context(
                {
                    "first_name": instance.user.first_name or "User",
                    "customer_name": tanant_name,
                    "setup_url": url,
                }
            )
            html_body = template.render(context)
        except Exception:
            # Fallback to plain text if template loading fails
            html_body = RESIDENT_INVITATION_EMAIL_BODY.format(
                first_name=instance.user.first_name,
                customer_name=tanant_name,
                url=url,
            )

        subject = RESIDENT_INVITATION_EMAIL_SUBJECT
        mngr.send_email(subject=subject, body=html_body)
