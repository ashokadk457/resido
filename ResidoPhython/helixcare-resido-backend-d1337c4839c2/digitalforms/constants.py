from common.utils.enum import EnumWithValueConverter


class FieldType(EnumWithValueConverter):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    text_field = "text_field"
    text_area = "text_area"
    integer_field = "integer_field"
    phone_field = "phone_field"
    email_field = "email_field"
    date_field = "date_field"
    time_field = "time_field"
    datetime_field = "datetime_field"
    boolean_field = "boolean_field"
    file_field = "file_field"
    draw_field = "draw_field"


class FormType(EnumWithValueConverter):
    file_upload = "file_upload"
    manual = "manual"


class FormReviewStatus(EnumWithValueConverter):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class FormStatus(EnumWithValueConverter):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


FORM_URL = "{domain}/#/digital-forms?version_id={form_version_id}"
SUBJECT_REVIEW_REQUESTED = "Review Requested for {form_name}"
BODY_REVIEW_REQUESTED = """
Dear {first_name},

You are requested to review the {form_name}. The due date to review the form is {due_date}. The setting for the form is {auto_approve} to auto-approve. Please click on the below url to review the form.

Form URL -> {url}
"""

SUBJECT_FORM_REJECTED = "Form Rejected - {form_name}"
BODY_FORM_REJECTED = """
Dear {first_name},

Your form in review with name "{form_name}" got rejected by the reviewer with comments. Click on the below url to review the comments.

Form URL -> {url}
"""
