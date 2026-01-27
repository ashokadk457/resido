import os

from common.utils.enum import EnumWithValueConverter

SCHEDULE_TYPE_CHOICES = (
    ("recurring", "Recurring"),
    ("occurs_once", "Occurs Once"),
    ("occurs_every", "Occurs Every"),
)
SCHEDULE_TRANSMIT_MODE_CHOICES = (
    ("download_as_xml", "Download as XML"),
    ("download_as_html", "Download as HTML"),
    ("download_as_pdf", "Download as PDF"),
    ("transmit_as_pdf_to_user", "Transmit as PDF to User"),
    ("transmit_as_pdf_to_patient", "Transmit as PDF to Patient"),
    ("transmit_as_pdf_to_external_email", "Transmit as PDF to External Email"),
    ("transmit_as_xml_to_user", "Transmit as XML to User"),
    ("transmit_as_xml_to_patient", "Transmit as XML to Patient"),
    ("transmit_as_xml_to_external_email", "Transmit as XML to External Email"),
    ("transmit_as_html_to_user", "Transmit as HTML to User"),
    ("transmit_as_html_to_patient", "Transmit as HTML to Patient"),
    ("transmit_as_html_to_external_email", "Transmit as HTML to External Email"),
)
REPEAT_TYPE_CHOICES = (
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
)


class Habit(EnumWithValueConverter):
    SMOKING = "Smoking"
    DRINKING = "Drinking"
    DRUGS = "Drugs"


class FamilyHistoryStatus(EnumWithValueConverter):
    PARTIAL = "partial"
    COMPLETED = "completed"
    HEALTH_UNKNOWN = "health_unknown"
    ENTERED_IN_ERROR = "entered_in_error"


class FamilyHistoryDataAbsentReasons(EnumWithValueConverter):
    SUBJECT_UNKNOWN = "subject_unknown"
    WITHHELD = "withheld"
    UNABLE_TO_OBTAIN = "unable_to_obtain"
    DEFERRED = "deferred"


class EncounterProcedureStatus(EnumWithValueConverter):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class PaymentOption(EnumWithValueConverter):
    CASH = "CASH"
    INSURANCE = "INSURANCE"


class TransactionType(EnumWithValueConverter):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


SCHEDULE_STATE_LABELS = {
    "started": "Started",
    "failed": "Failed",
    "completed": "Completed",
}

PATIENT_CHART_EMAIL_MESSAGE = """
Hi!

Please find your patient chart attached in this email. If the patient chart is password protected, you will
receive another email shortly containing the password.

Thanks!
"""

SCHEDULE_STATE_EMAIL_MESSAGE = """
Hi!

Patient Chart Export Schedule {schedule_name} having ID {schedule_id} has {state}.

Thanks!
"""

SCHEDULE_STATE_NO_DATA_EMAIL_MESSAGE = """
Hi!

Patient Chart Export Schedule {schedule_name} having ID {schedule_id} has {state} with no data.

Thanks!
"""

SCHEDULE_STATE_ERROR_EMAIL_MESSAGE = """
Hi!

Patient Chart Export Schedule {schedule_name} having ID {schedule_id} has {state} due to following error.

Error Detail - {error_message}

Thanks!
"""

PATIENT_CHART_ATTACHMENT_PASSWORD_EMAIL_MESSAGE = """
Hi!

Following is your password to open the patient chart generated for the Request ID {request_id}

Password: {password}

Thanks!
"""


class ResidentProfileType(EnumWithValueConverter):
    OWNER = "owner"
    TENANT = "tenant"


class ResidentEvictionDeliveryMethodType(EnumWithValueConverter):
    SMS = "SMS"
    EMAIL_NOTIFICATION = "EMAIL"
    IN_PERSON_DELIVERY = "In-Person Delivery"


class ResidentEvictionStatusType(EnumWithValueConverter):
    PENDING = "Pending"
    SENT = "Sent"
    REJECTED = "rejected"


RESIDENT_INVITATION_LINK_EXPIRY = int(
    os.getenv("RESIDENT_INVITATION_LINK_EXPIRY", "10000")
)
RESIDENT_INVITATION_FORM_URL = "https://{domain}/#/create-password?user_id={user_id}&user_type={user_type}&code={code}"
RESIDENT_INVITATION_EMAIL_SUBJECT = (
    "Please click the button and complete your password setup"
)
RESIDENT_INVITATION_EMAIL_BODY = "Hello {first_name},\n\n The {customer_name} has sent you a password reset link. Please click the button below to complete your password setup.\n\n{url}"
