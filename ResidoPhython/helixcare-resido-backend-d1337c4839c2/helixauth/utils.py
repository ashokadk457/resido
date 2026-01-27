import random
import re
import string
import secrets
import datetime
from copy import deepcopy
from random import randint
from django.db import connection
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from common.exception import StandardAPIException
from common.errors import ERROR_DETAILS
from common.utils.general import is_valid_uuid
from common.utils.logging import logger

from notifications.utils import (
    get_resident_communication_details,
    get_staff_communication_details,
)
from notifications.models import NotificationQueue
from notifications.utils import Utils
from notifications.managers.template.registry import TemplateRegistry
from notifications.constants import TemplateCode
from residents.models import Resident
from staff.models import HelixStaff
from helixauth.token.user.refresh import HelixUserRefreshToken
from .constants import (
    NotificationChannel,
    DEFAULT_COUNTRY_CODE,
    RESET_PASSWORD_URL,
    UsernameType,
)
from .models import SecurityQuestion, UserSecurityQuestion, VerificationCode, HelixUser


def get_token_for_user(user):
    # TODO MUST later what's the use of this? Is this being used for generating refresh token?
    refresh = HelixUserRefreshToken.for_user(user)

    return {
        "access": str(refresh.access_token),
        "expires_in": datetime.datetime.fromtimestamp(refresh.payload.get("exp")),
        "refresh": str(refresh),
    }


def generate_code(length=6):
    return "".join(secrets.choice("0123456789") for _ in range(length))


def get_user(user_id):
    return HelixUser.objects.filter(id=user_id).first()


def get_users(user_ids):
    return HelixUser.objects.filter(id__in=user_ids)


def verify_code(user_id, user_type, code):
    try:
        VerificationCode.objects.get(user_id=user_id, user_type=user_type, code=code)
        return True
    except VerificationCode.DoesNotExist:
        return False


def create_verification_code(user_id, user_type, channel, mode="update_or_create"):
    code = generate_code()
    if mode == "update_or_create":
        VerificationCode.objects.update_or_create(
            user_id=user_id,
            user_type=user_type,
            channel=channel,
            defaults={
                "code": code,
                "deleted_by": None,
            },
        )
    elif mode == "update":
        q = VerificationCode.objects.filter(
            user_id=user_id, user_type=user_type, channel=channel
        )
        if q.exists():
            q.update(code=code, deleted_by=None)

    return code


def get_resident_or_staff_by_user(user):
    match = None
    try:
        match = HelixStaff.objects.get(user=user)
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            match = Resident.objects.get(user=user)
        except Resident.DoesNotExist:
            pass
    return match


def get_patient_or_provider_by_email(email):
    match = None
    count = 0
    try:
        count = (
            HelixStaff.objects.filter(user__email__iexact=email)
            .filter(
                user__is_active=1, user_roles__is_role_active=1, user__status="APPROVED"
            )
            .count()
        )
        match = (
            HelixStaff.objects.filter(user__email__iexact=email)
            .filter(
                user__is_active=1, user_role__is_role_active=1, user__status="APPROVED"
            )
            .first()
        )
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            count = (
                Resident.objects.filter(email__iexact=email)
                # .filter(user__is_active=1)
                .count()
            )
            match = (
                Resident.objects.filter(email__iexact=email)
                # .filter(user__is_active=1)
                .first()
            )
        except Resident.DoesNotExist:
            pass
    return match, count


# Move this to any util class
def get_patient_or_provider_by_mobile(mobile):
    match = None
    count = 0
    try:
        count = (
            HelixStaff.objects.filter(user__phone=mobile)
            .filter(
                user__is_active=1, user_roles__is_role_active=1, user__status="APPROVED"
            )
            .count()
        )
        match = (
            HelixStaff.objects.filter(user__phone=mobile)
            .filter(
                user__is_active=1, user_roles__is_role_active=1, user__status="APPROVED"
            )
            .first()
        )
    except HelixStaff.DoesNotExist:
        pass
    if match is None:
        try:
            count = Resident.objects.filter(email__iexact=mobile).count()
            match = Resident.objects.filter(email__iexact=mobile).first()
        except Resident.DoesNotExist:
            pass
    return match, count


def verify_security_answer(user, question, answer):
    count = (
        UserSecurityQuestion.objects.filter(user=user)
        .filter(question=question)
        .filter(response=answer)
        .count()
    )
    return count == 1


def get_user_via_mobile(mobile):
    user, count = get_patient_or_provider_by_mobile(mobile)
    if count == 0:
        return Response({"message": ERROR_DETAILS["no_active_user"]}, status=400)
    if count > 1:
        return Response({"message": "More then one account registered"}, status=400)
    if count == 1:
        send_otp(user, "SMS")
        return Response({"message": "OTP sent!"}, status=200)


def get_user_id_via_receiving_address(receiving_address):
    helix_user = HelixUser.objects.filter(
        Q(email__iexact=receiving_address) | Q(phone=receiving_address)
    ).first()
    if not helix_user:
        raise StandardAPIException(
            code="invalid_user_id",
            detail=ERROR_DETAILS["invalid_user_id"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return helix_user.id


def send_otp(
    user,
    type,
    receiving_address=None,
    lang=None,
    mode=None,
    user_type=None,
    country_code=DEFAULT_COUNTRY_CODE,
):
    notification_type = type
    notif = NotificationQueue()
    user_id = None
    original_receiving_address = deepcopy(receiving_address)
    if user.__class__.__name__ == "Resident":
        mode, lang = Utils.check_notification_type(user)
        notif.user = user
        user_type = 2 if user_type is None else user_type
        user_id = user.id
        email, phone_number, _country_code = get_resident_communication_details(
            id=str(user.id)
        )
        if notification_type == NotificationChannel.SMS.value:
            country_code = country_code if not _country_code else _country_code
            receiving_address = f"{country_code}{phone_number}"
        elif notification_type == NotificationChannel.EMAIL.value:
            receiving_address = email
    elif user:
        mode, lang = Utils.check_notification_type_provider(user)
        notif.provider = user
        user_id = user.user.id
        user_type = 1 if user_type is None else user_type
        email, phone_number, _country_code = get_staff_communication_details(
            id=str(user.id)
        )
        if notification_type == NotificationChannel.SMS.value:
            country_code = country_code if not _country_code else _country_code
            receiving_address = f"{country_code}{phone_number}"
        elif notification_type == NotificationChannel.EMAIL.value:
            receiving_address = email
    else:
        user_id = receiving_address
        user_type = user_type if user_type is not None else 3
        if notification_type == NotificationChannel.SMS.value:
            receiving_address = f"{country_code}{receiving_address}"
            original_receiving_address = receiving_address

    code = create_verification_code(user_id=user_id, user_type=user_type, channel=type)
    setting = Utils.get_tenant_notification(notification_type, "4", lang)
    if not setting:
        raise StandardAPIException(
            code="missing_notification_setting",
            detail=ERROR_DETAILS["missing_notification_setting"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    payload = {}
    payload["message"] = "Verification code is: " + str(code)
    payload["subject"] = "OTP Verification"

    # Add HTML template for email notifications
    if notification_type == NotificationChannel.EMAIL.value:
        try:
            user_first_name = "User"
            if user and hasattr(user, "first_name"):
                user_first_name = user.first_name or "User"
            elif user and hasattr(user, "user") and hasattr(user.user, "first_name"):
                user_first_name = user.user.first_name or "User"

            template_code = (
                TemplateCode.USER_ACCOUNT_CREATION.value
                if user_type == 2
                else TemplateCode.OTP_VERIFICATION.value
            )

            context = {
                "email_subject": "OTP Verification",
                "user_first_name": user_first_name,
                "otp": code,
                "logo_url": None,
            }

            subject, html_body = TemplateRegistry.get_email_content(
                template_code, context
            )
            if html_body and TemplateRegistry.is_html_template_used(template_code):
                payload["html_message"] = html_body
                payload["subject"] = subject
        except Exception as e:
            # Fallback to plain text if template fails
            logger.error(
                f"Failed to generate HTML email template for OTP: {str(e)}",
                exc_info=True,
            )

    notif.notification_setting = setting
    notif.payload = payload
    notif.receiving_address = (
        original_receiving_address if original_receiving_address else receiving_address
    )
    notif.save()


def send_reset_password_link_to_helix_user(
    user,
    type,
    receiving_address=None,
    lang=None,
    mode=None,
    user_type=None,
    country_code=DEFAULT_COUNTRY_CODE,
):
    notification_type = type
    notif = NotificationQueue()
    user_id = None
    original_receiving_address = deepcopy(receiving_address)
    _, lang = Utils.check_notification_type_provider(user)
    notif.provider = user
    user_id = user.user.id
    user_type = 1 if user_type is None else user_type
    email, phone_number, _country_code = get_staff_communication_details(
        id=str(user.id)
    )
    if notification_type == NotificationChannel.SMS.value:
        country_code = country_code if not _country_code else _country_code
        receiving_address = f"{country_code}{phone_number}"
    elif notification_type == NotificationChannel.EMAIL.value:
        receiving_address = email

    code = create_verification_code(user_id=user_id, user_type=user_type, channel=type)
    setting = Utils.get_tenant_notification(notification_type, "4", lang)
    if not setting:
        raise StandardAPIException(
            code="missing_notification_setting",
            detail=ERROR_DETAILS["missing_notification_setting"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    domain = connection.tenant.domain
    url = RESET_PASSWORD_URL.format(
        domain=domain, user_id=user_id, code=code, user_type=user_type
    )

    payload = {}
    payload["subject"] = "Reset Your Password"

    if notification_type == NotificationChannel.EMAIL.value:
        try:
            context = {
                "email_subject": "Reset Your Password",
                "user_first_name": user.user.first_name or "User",
                "otp": code,
                "reset_password_url": url,
                "logo_url": None,
            }

            template_code = TemplateCode.FORGOT_PASSWORD.value
            subject, html_body = TemplateRegistry.get_email_content(
                template_code, context
            )

            if html_body and TemplateRegistry.is_html_template_used(template_code):
                payload["html_message"] = html_body
                payload["subject"] = subject
            else:
                payload["message"] = f"Reset Password Link: {url}"
        except Exception as e:
            logger.error(
                f"Failed to generate HTML email template for password reset: {str(e)}",
                exc_info=True,
            )
            payload["message"] = f"Reset Password Link: {url}"
    else:
        payload["message"] = f"Your password reset OTP is: {code}"

    notif.notification_setting = setting
    notif.payload = payload
    notif.receiving_address = (
        original_receiving_address if original_receiving_address else receiving_address
    )
    notif.save()


# def random_password():
#     characters = string.ascii_letters + string.digits + string.punctuation
#     password = "".join(random.choice(characters) for i in range(12))
#     return password
def random_password(length=12):
    """
    Generates a guaranteed complex password (A-Z, a-z, 0-9, Punctuation)
    that meets minimum complexity requirements (min 8 chars, one of each type).
    """
    MIN_REQUIRED_CHARS = 4
    if length < MIN_REQUIRED_CHARS:
        length = MIN_REQUIRED_CHARS
    if length < 8:
        length = 8
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    punctuation = string.punctuation
    all_allowed_pool = uppercase + lowercase + digits + punctuation

    password_list = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(punctuation),
    ]
    remaining_length = length - len(password_list)
    password_list.extend(random.choices(all_allowed_pool, k=remaining_length))
    random.shuffle(password_list)
    return "".join(password_list)


def send_temp_password_email(user, temporary_password):
    notif = NotificationQueue()
    _, lang = Utils.check_notification_type_provider(user)
    notification_type = NotificationChannel.EMAIL.value
    email, _, _ = get_staff_communication_details(id=str(user.id))
    receiving_address = email
    setting = Utils.get_tenant_notification(notification_type, "4", lang)
    if not setting:
        raise StandardAPIException(
            code="missing_notification_setting",
            detail=ERROR_DETAILS["missing_notification_setting"],
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    payload = {}
    payload["message"] = "Your Password is: " + temporary_password
    payload["subject"] = "Temporary Password!"
    notif.notification_setting = setting
    notif.payload = payload
    notif.receiving_address = receiving_address
    notif.save()


def get_random_security_question(user):
    count = UserSecurityQuestion.objects.filter(user=user).count()
    rand_index = randint(0, count - 1)
    rec = UserSecurityQuestion.objects.filter(user=user).all()[rand_index]
    ques = SecurityQuestion.objects.get(id=rec.question.id)
    return {
        "question_id": rec.question.id,
        "question_name": ques.name,
        "type": "security_question",
    }


def identify_username_type(username):
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    phone_pattern = r"^\+?\d{10,15}$"

    if re.match(email_pattern, username):
        return UsernameType.EMAIL.value
    elif re.match(phone_pattern, username):
        return UsernameType.PHONE.value
    elif is_valid_uuid(username):
        return UsernameType.UUID.value


def generate_pdf_from_html(html_content):
    """
    Generate PDF bytes from HTML content using xhtml2pdf

    Args:
        html_content (str): HTML content to convert to PDF

    Returns:
        bytes: PDF file bytes or None if generation fails
    """
    from xhtml2pdf import pisa
    from io import BytesIO
    from common.utils.logging import logger

    if not html_content:
        logger.warning("Empty HTML content provided for PDF generation")
        return None

    try:
        # Create BytesIO objects for result
        pdf_buffer = BytesIO()

        # Add basic HTML structure if not present
        if not html_content.strip().lower().startswith("<html"):
            html_content = f"""
            <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            line-height: 1.6;
                        }}
                        h1 {{
                            color: #333;
                            border-bottom: 2px solid #007bff;
                            padding-bottom: 10px;
                        }}
                        h2 {{
                            color: #555;
                            margin-top: 20px;
                        }}
                        p {{
                            color: #666;
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
            </html>
            """

        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            BytesIO(html_content.encode("utf-8")),
            pdf_buffer,
            show_error_as_pdf=False,
            log_config=None,
        )

        if pisa_status.err:
            logger.error(f"Error generating PDF: {pisa_status}")
            return None

        # Get bytes from buffer
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.getvalue()

        if not pdf_bytes:
            logger.warning("No PDF bytes generated from HTML")
            return None

        logger.info(f"Successfully generated PDF from HTML ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    except Exception as e:
        from common.utils.logging import logger

        logger.error(
            f"Exception while generating PDF from HTML: {str(e)}", exc_info=True
        )
        return None
