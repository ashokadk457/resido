import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.forms import ValidationError
from django.utils import timezone

from staff.models import HelixStaff
from assets.models import Asset
from audit.models import GenericModel

optional = {"null": True, "blank": True}


DELIVERY_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("sent", "Sent"),
    ("failed_email", "Failed (Email)"),
    ("delivered_sms", "Delivered (SMS)"),
    ("failed_sms", "Failed (SMS)"),
]


class GenericMessage(GenericModel):
    subject = models.CharField(max_length=255, **optional)  # Optional for SMS
    body = models.TextField(**optional)
    sent_at = models.DateTimeField(**optional)
    is_draft = models.BooleanField(default=False)
    is_archive = models.BooleanField(default=False)  # Optional for SMS
    retry_count = models.PositiveIntegerField(default=0)
    delivery_status = models.CharField(
        max_length=128, choices=DELIVERY_STATUS_CHOICES, default="pending"
    )

    class Meta:
        abstract = True


class Recipient(GenericModel):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
        **optional,
        help_text="The model type for the recipient (e.g., HelixUser, Patient, Provider).",
    )
    object_id = models.UUIDField(
        help_text="The ID of the recipient instance.",
        **optional,
    )
    recipient = GenericForeignKey(
        "content_type",
        "object_id",
    )
    read_status = models.BooleanField(
        default=False, help_text="Has the recipient read this email?"
    )
    read_at = models.DateTimeField(
        **optional, help_text="Timestamp when the email was read."
    )
    delivery_status = models.CharField(
        max_length=128, choices=DELIVERY_STATUS_CHOICES, default="pending"
    )

    def mark_as_read(self):
        if not self.read_status:
            self.read_status = True
            self.read_at = timezone.now()
            self.save()

    class Meta:
        abstract = True


class Email(GenericMessage):
    attchments = models.ManyToManyField(
        Asset,
        through="EmailAttachment",
        related_name="email_attachments",
        help_text="Attachments for the email",
    )
    recipients = models.ManyToManyField(
        ContentType,
        through="EmailRecipient",
        related_name="email_recipients",
        help_text="Attachments for the email",
    )
    parent_email = models.ForeignKey(
        "self",
        **optional,
        related_name="replies",
        on_delete=models.SET_NULL,
        help_text="Reference to the parent email if this is a reply",
    )

    @property
    def is_internal(self, obj):
        # TODO: Add logic to fetch this from domain.
        return True

    def __str__(self):
        return f" {self.subject} - by {self.created_by}"


class EmailRecipient(Recipient):
    RECIPIENT_TYPE_CHOICES = [
        ("to", "To"),
        ("cc", "CC"),
        ("bcc", "BCC"),
    ]

    email = models.ForeignKey(
        "Email",
        related_name="email_recipients",
        on_delete=models.CASCADE,
        help_text="The email to which this recipient belongs",
    )
    email_address = models.EmailField(
        **optional,
        help_text="Plain email address if the recipient is not a model instance.",
    )
    recipient_type = models.CharField(
        max_length=10,
        choices=RECIPIENT_TYPE_CHOICES,
        help_text="Recipient type: 'to', 'cc', or 'bcc'.",
        default="to",
    )

    class Meta:
        unique_together = (("email", "email_address", "object_id", "recipient_type"),)

    def clean(self):
        if not self.content_type and not self.object_id and not self.email_address:
            raise ValidationError(
                "Either content_type/object_id or email_address must be provided."
            )

    def __str__(self):
        return f"Recipient: {self.email_address or self.recipient_id} ({self.recipient_type}) for Email {self.email}"


class EmailAttachment(GenericModel):
    email = models.ForeignKey(
        Email, related_name="attachments", on_delete=models.CASCADE
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="email")

    def __str__(self):
        return f"{self.asset.filename} for email :- {self.email}"


class SMS(GenericMessage):
    parent_sms = models.ForeignKey(
        "self",
        **optional,
        related_name="replies",
        on_delete=models.SET_NULL,
        help_text="Reference to the parent message if this is a reply to",
    )  # This will be used to show preview of replied to SMS.

    recipient = models.ManyToManyField(
        ContentType,
        through="SMSRecipient",
        related_name="sms_recipients",
        help_text="Attachments for the email",
    )

    def __str__(self):
        return f"SMS from {self.created_by}"


class SMSRecipient(Recipient):
    sms = models.ForeignKey(
        "SMS",
        related_name="sms_recipients",
        on_delete=models.CASCADE,
        help_text="The SMS to which this recipient belongs",
    )
    country_code = models.CharField(max_length=10, **optional)
    phone = models.CharField(max_length=20, **optional)

    class Meta:
        unique_together = ("sms", "object_id", "country_code", "phone")

    def __str__(self):
        return f"Recipient {self.object_id or self.phone} ({self.content_type}) for SMS {self.sms} - Status: {self.delivery_status}"


class DeliveryLog(GenericModel):
    """
    Unified logging for Emails and SMS using GenericForeignKey.
    """

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, **optional)
    object_id = models.UUIDField(**optional)
    related_object = GenericForeignKey("content_type", "object_id")
    event = models.CharField(max_length=255, **optional)
    details = models.TextField(**optional)

    def __str__(self):
        return f"Log for {self.related_object} - {self.event}"


class EmailTemplate(GenericModel):
    display_id = models.UUIDField(default=uuid.uuid4, editable=False)
    template_name = models.CharField(max_length=100)
    provider = models.ForeignKey(
        HelixStaff, related_name="provider_email_template", on_delete=models.CASCADE
    )
    template_body = models.TextField()
    is_active = models.BooleanField(default=True)  # Default it will be True

    class Meta:
        path_to_location = "provider__locations"

    def __str__(self):
        return f"Email template from {self.provider}"
