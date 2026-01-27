from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status

from assets.models import Asset
from assets.serializers import AssetSerializer
from common.errors import ERROR_DETAILS
from common.exception import StandardAPIException
from common.utils.logging import logger
from helixauth.models import HelixUser
from helixauth.serializers import HelixUserReceipientSerialiser
from notifications.apiviews import sendEmail, sendSMS
from patients.models import Patient
from patients.serializers import PatientRecipientSerialiser
from staff.models import HelixStaff

from .models import (
    SMS,
    Email,
    EmailAttachment,
    EmailRecipient,
    SMSRecipient,
    EmailTemplate,
)
from .utils import download_remote_file_as_email_attachment


class BaseSMSEmailSerializer(serializers.Serializer):
    @staticmethod
    def validate_recipient_data(data):
        """
        Validate if all recipients have the correct content type and exist in the DB as per content type.
        """
        recipients = data.get("recipients", [])
        if not recipients:
            # For SMS, we accept only a single recipient
            recipients = data.get("recipient", {})
            recipients = [recipients]
        for recipient in recipients:
            # If the user entered the email or mobile number directly, no object ID and content type will be present.
            if not recipient.get("content_type"):
                continue
            content_type = ContentType.objects.filter(
                model=recipient["content_type"]
            ).first()
            if not content_type:
                raise serializers.ValidationError(
                    code="invalid_content_type",
                    detail=ERROR_DETAILS["invalid_content_type"],
                )

            # Validate HeliUser: If provider.id is passed, fetch its associated HelixUser (provider.user.id).
            if recipient["content_type"] == "helixuser":
                helix_user = HelixUser.objects.filter(id=recipient["object_id"]).first()
                if not helix_user:
                    helix_staff = HelixStaff.objects.filter(
                        id=recipient["object_id"]
                    ).first()
                    if not helix_staff:
                        raise serializers.ValidationError(
                            code="provider_not_found",
                            detail=ERROR_DETAILS["provider_not_found"],
                        )
                    recipient["object_id"] = helix_staff.user.id

            elif recipient["content_type"] == "patient":
                if not Patient.objects.filter(id=recipient["object_id"]).first():
                    raise serializers.ValidationError(
                        code="patient_not_found",
                        detail=ERROR_DETAILS["patient_not_found"],
                    )
            recipient["content_type"] = content_type

        return data


class EmailAttachmentSerializer(serializers.ModelSerializer):
    asset_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        source="asset",
        write_only=True,
    )

    class Meta:
        model = EmailAttachment
        fields = ("asset_id",)


class EmailRecipientSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(required=False)

    class Meta:
        model = EmailRecipient
        fields = [
            "id",
            "object_id",
            "content_type",
            "email_address",
            "recipient_type",
            "read_status",
            "read_at",
            "delivery_status",
        ]


class CreateEmailSerializer(BaseSMSEmailSerializer, serializers.ModelSerializer):
    recipients = EmailRecipientSerializer(many=True)  # Allow creation of recipients
    attachments = EmailAttachmentSerializer(many=True)  # Allow creation of attachments
    delivery_status = serializers.CharField(read_only=True)  # Read-only field
    # created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def to_representation(self, instance):
        # Add related model serializers dynamically to context
        self.context.update(
            {
                "helixuser_serializer": HelixUserReceipientSerialiser,
                "patient_serializer": PatientRecipientSerialiser,
            }
        )
        return super().to_representation(instance)

    class Meta:
        model = Email
        fields = (
            "id",
            "subject",
            "body",
            "sent_at",
            "is_draft",
            "recipients",
            "attachments",
            "created_by",
            "delivery_status",
            "parent_email",
        )

    def validate(self, data):
        """
        Validate that if is_draft is False, at least one recipient is provided.
        """
        is_draft = data.get("is_draft", True)  # Default is True if not provided
        recipients = data.get("recipients", [])

        if not is_draft and not recipients:
            raise serializers.ValidationError(
                {
                    "recipients": "At least one recipient must be provided when sending an email."
                }
            )
        data = self.validate_recipient_data(data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        recipients_data = validated_data.pop("recipients", [])
        attachments_data = validated_data.pop("attachments", [])
        files = None
        is_email_sent = False
        if validated_data["is_draft"]:
            validated_data["delivery_status"] = "draft"
        # Create the Email instance
        email = Email.objects.create(**validated_data)

        # Handle recipients creation
        to, cc, bcc = [], [], []
        for recipient_data in recipients_data:
            recipient_data["email"] = email
            recipient_data["created_by_id"] = email.created_by.id
            recipient = EmailRecipient.objects.create(**recipient_data)
            if recipient_data["recipient_type"] == "to":
                to.append(recipient_data["email_address"])
            elif recipient_data["recipient_type"] == "cc":
                cc.append(recipient_data["email_address"])
            elif recipient_data["recipient_type"] == "bcc":
                bcc.append(recipient_data["email_address"])

        # Handle attachments creation
        for attachment_data in attachments_data:
            attachment_data["email"] = email
            attachment_data["created_by"] = validated_data["created_by"]
            EmailAttachment.objects.create(**attachment_data)
        if attachments_data:
            assets = Asset.objects.filter(email__email=email)
            file_urls = [asset.file.url for asset in assets]
            files = download_remote_file_as_email_attachment(file_urls)

        if not files and attachments_data:
            raise StandardAPIException(
                code="failed_sending_email_with_attchment",
                detail="Failed to send Email with Attchment. Please try again or with different files.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not email.is_draft or not self.context.get("no_email_sending"):
            try:
                response = sendEmail(
                    subject=email.subject,
                    message=email.body,
                    emails=to,
                    sender_id=str(email.created_by.id),
                    rec_id=str(email.id),
                    files=files,
                    cc=cc,
                    bcc=bcc,
                )
                logger.info(f"response From Email Service:- {response}")
                status_code = response.get("status_code")
                message = response.get("message", {}).get("message")
                if status_code in [200, 201] and message == "Email Sent!":
                    for recipient in email.email_recipients.all():
                        recipient.delivery_status = "sent"
                        is_email_sent = True
                        recipient.save()
            except Exception as e:
                logger.error(f"Exception while sending email..{e}")
                raise serializers.ValidationError(
                    code="not_able_to_send_email",
                    detail=ERROR_DETAILS["not_able_to_send_email"],
                )

        if is_email_sent and not email.is_draft:
            email.delivery_status = "sent"
            email.sent_at = timezone.now()
            email.save()
        return email


class ListEmailSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField()
    attachments = AssetSerializer(many=True, read_only=True, source="attchments")
    delivery_status = serializers.CharField(read_only=True)
    sender = serializers.SerializerMethodField()  # Add sender field
    thread_emails = (
        serializers.SerializerMethodField()
    )  # To fetch all emails in the thread

    def get_recipients(self, instance):
        recipients = EmailRecipient.objects.filter(email=instance)
        recipient_list = []

        for recipient in recipients:
            recipient_data = {
                "id": recipient.id,
                "email_address": recipient.email_address,
                "recipient_type": recipient.recipient_type,
                "read_at": recipient.read_at,
                "read_status": recipient.read_status,
            }

            # Include related object data if content_type and object_id exist
            if recipient.content_type and recipient.object_id:
                related_object = recipient.content_type.get_object_for_this_type(
                    id=recipient.object_id
                )
                serializer_class = self.context.get(
                    f"{recipient.content_type.model}_serializer"
                )

                if serializer_class:
                    recipient_data["related_object"] = serializer_class(
                        related_object, context=self.context
                    ).data
                else:
                    recipient_data["related_object"] = None
            else:
                recipient_data["related_object"] = None

            recipient_list.append(recipient_data)

        return recipient_list

    def get_sender(self, instance):
        # Serialize the created_by field as the sender
        if instance.created_by:
            sender_serializer = self.context.get("helixuser_serializer")
            if sender_serializer:
                return sender_serializer(instance.created_by, context=self.context).data
        return None

    def get_thread_emails(self, instance):
        # Fetch all emails in the thread sharing the same parent_email
        thread_emails = Email.objects.filter(parent_email=instance).order_by(
            "created_on"
        )
        return self.__class__(thread_emails, many=True, context=self.context).data

    class Meta:
        model = Email
        fields = (
            "id",
            "subject",
            "body",
            "sent_at",
            "is_draft",
            "is_archive",
            "recipients",
            "attachments",
            "created_by",
            "created_on",
            "sent_at",
            "delivery_status",
            "sender",  # Include sender in the fields
            "parent_email",
            "thread_emails",
        )


class UpdateDraftEmailSerializer(BaseSMSEmailSerializer, serializers.ModelSerializer):
    recipients = EmailRecipientSerializer(many=True, required=False)
    attachments = EmailAttachmentSerializer(many=True, required=False)
    delivery_status = serializers.CharField(read_only=True)  # Read-only field
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Email
        fields = (
            "id",
            "subject",
            "body",
            "sent_at",
            "is_draft",
            "is_archive",
            "recipients",
            "attachments",
            "created_by",
            "delivery_status",
        )

    def validate(self, data):
        """
        Validate that if is_draft is False, at least one recipient is provided.
        """
        is_archive = data.get("is_archive", False)  # Default is False if not provided
        is_draft = data.get("is_draft", True)  # Default is True if not provided
        recipients = data.get("recipients", [])

        if not is_draft and not recipients:
            raise serializers.ValidationError(
                {
                    "recipients": "At least one recipient must be provided when sending an email."
                }
            )
        else:
            if not is_archive:
                raise StandardAPIException(
                    code="is_archive_error",
                    detail=ERROR_DETAILS["is_archive_error"],
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        data = self.validate_recipient_data(data)
        return data

    @transaction.atomic
    def update(self, instance, validated_data):
        # Mark email as no longer a draft
        if validated_data["is_archive"]:
            instance.is_archive = validated_data["is_archive"]
            instance.save()
            return instance
        is_email_sent = False
        instance.is_draft = validated_data["is_draft"]
        files = None

        # Update email fields
        instance.subject = validated_data.get("subject", instance.subject)
        instance.body = validated_data.get("body", instance.body)

        # Handle recipients update
        to, cc, bcc = [], [], []
        recipients_data = validated_data.pop("recipients", [])
        instance.email_recipients.all().delete()  # Clear existing recipients
        for recipient_data in recipients_data:
            recipient_data["email"] = instance
            recipient_data["created_by"] = instance.created_by
            recipient = EmailRecipient.objects.create(
                **recipient_data,
            )
            if recipient_data["recipient_type"] == "to":
                to.append(recipient_data["email_address"])
            elif recipient_data["recipient_type"] == "cc":
                cc.append(recipient_data["email_address"])
            elif recipient_data["recipient_type"] == "bcc":
                bcc.append(recipient_data["email_address"])

        # Handle attachments creation
        attachments_data = validated_data.pop("attachments", [])
        instance.attachments.all().delete()  # Clear existing attachments
        for attachment_data in attachments_data:
            attachment_data["email"] = instance
            attachment_data["created_by"] = instance.created_by
            EmailAttachment.objects.create(**attachment_data)
        if attachments_data:
            assets = Asset.objects.filter(email__email=instance)
            file_urls = [asset.file.url for asset in assets]
            files = download_remote_file_as_email_attachment(file_urls)
        if not files and attachments_data:
            raise StandardAPIException(
                code="failed_sending_email_with_attchment",
                detail="Failed to send Email with Attchment. Please try again or with different files.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if not validated_data["is_draft"]:
            try:
                response = sendEmail(
                    subject=instance.subject,
                    message=instance.body,
                    emails=to,
                    sender_id=str(instance.created_by.id),
                    rec_id=str(instance.id),
                    files=files,
                    cc=cc,
                    bcc=bcc,
                )
                logger.info(f"response From Email Service:- {response}")
                status_code = response.get("status_code")
                message = response.get("message", {}).get("message")
                if status_code in [200, 201] and message == "Email Sent!":
                    for recipient in instance.email_recipients.all():
                        recipient.delivery_status = "sent"
                        is_email_sent = True
                        recipient.save()
            except Exception as e:
                logger.error(f"Exception while sending email..{e}")

        # Finalize delivery status
        if is_email_sent:
            instance.delivery_status = "sent"
            instance.sent_at = timezone.now()
        elif not validated_data["is_draft"]:
            instance.delivery_status = "pending"
        instance.save()
        return instance


class MarkAsReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailRecipient
        fields = ["read_status", "read_at"]  # Allow updating only these fields
        read_only_fields = [
            "read_at"
        ]  # `read_at` should be set automatically in the view


class SMSRecipientSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(required=False)

    class Meta:
        model = SMSRecipient
        fields = [
            "id",
            "object_id",
            "content_type",
            "phone",
            "country_code",
            "delivery_status",
        ]


class CreateSMSSerializer(BaseSMSEmailSerializer, serializers.ModelSerializer):
    recipient = SMSRecipientSerializer()  # Allow creation of recipients
    delivery_status = serializers.CharField(read_only=True)  # Read-only field
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def to_representation(self, instance):
        # Add related model serializers dynamically to context
        self.context.update(
            {
                "helixuser_serializer": HelixUserReceipientSerialiser,
                "patient_serializer": PatientRecipientSerialiser,
            }
        )
        return super().to_representation(instance)

    class Meta:
        model = SMS
        fields = (
            "id",
            "body",
            "sent_at",
            "recipient",
            "created_by",
            "delivery_status",
        )

    def validate(self, data):
        """
        Validate that if is_draft is False, at least one recipient is provided.
        """
        recipient = data.get("recipient")

        if not recipient:
            raise serializers.ValidationError(
                {
                    "recipients": "At least one recipient must be provided when sending an SMS."
                }
            )
        data = self.validate_recipient_data(data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        recipient_data = validated_data.pop("recipient", {})
        recipient_data["created_by"] = validated_data["created_by"]
        sms = SMS.objects.create(**validated_data)
        recipient_data["sms"] = sms
        recipient = SMSRecipient.objects.create(**recipient_data)

        if recipient.country_code and recipient.phone:
            valid_phone = recipient.country_code + recipient.work_phone

        elif recipient.content_type and recipient.object_id:
            related_object = recipient.content_type.get_object_for_this_type(
                id=recipient.object_id
            )
            if isinstance(related_object, Patient):
                if getattr(related_object, "country_code", None) and getattr(
                    related_object, "mobile_number"
                ):
                    country_code = (
                        f"+{related_object.country_code}"
                        if not related_object.country_code.startswith("+")
                        else related_object.country_code
                    )
                    valid_phone = country_code + related_object.mobile_number
                else:
                    raise serializers.ValidationError(
                        code="invalid_phone_number_country_code",
                        detail=ERROR_DETAILS["invalid_phone_number_country_code"],
                    )
            else:
                if getattr(related_object, "country_code", None) and getattr(
                    related_object, "work_phone"
                ):
                    country_code = (
                        f"+{related_object.country_code}"
                        if not related_object.country_code.startswith("+")
                        else related_object.country_code
                    )
                    valid_phone = country_code + related_object.work_phone
                else:
                    raise serializers.ValidationError(
                        code="invalid_phone_number_country_code",
                        detail=ERROR_DETAILS["invalid_phone_number_country_code"],
                    )
        if not valid_phone:
            raise serializers.ValidationError(
                code="invalid_phone_number_country_code",
                detail=ERROR_DETAILS["invalid_phone_number_country_code"],
            )

        try:
            response = sendSMS(
                valid_phone,
                validated_data["body"],
                str(validated_data["created_by"].id),
                str(sms.id),
            )
            error_message = response.get("message", {}).get("error_message")
            if not error_message:
                sms.delivery_status = "sent"
                recipient.delivery_status = "sent"
                sms.sent_at = timezone.now()
                sms.save()
                recipient.save()
        except Exception as e:
            logger.error(f"Exception while sending SMS..{e}")
            raise serializers.ValidationError(
                code="not_able_to_send_sms",
                detail=ERROR_DETAILS["not_able_to_send_sms"],
            )
        if error_message:
            logger.error(f"Error form SMS Service:- {error_message}")
            raise serializers.ValidationError(
                code="not_able_to_send_sms",
                detail=ERROR_DETAILS["not_able_to_send_sms"],
            )
        return sms


class ListSMSSerializer(serializers.ModelSerializer):
    recipient = serializers.SerializerMethodField()
    delivery_status = serializers.CharField(read_only=True)
    sender = serializers.SerializerMethodField()  # Add sender field

    def get_recipient(self, instance):
        recipient = SMSRecipient.objects.filter(sms=instance).first()

        recipient_data = {
            "id": recipient.id,
            "phone": recipient.phone,
            "country_code": recipient.country_code,
            "read_at": recipient.read_at,
            "read_status": recipient.read_status,
        }

        # Include related object data if content_type and object_id exist
        if recipient.content_type and recipient.object_id:
            related_object = recipient.content_type.get_object_for_this_type(
                id=recipient.object_id
            )
            serializer_class = self.context.get(
                f"{recipient.content_type.model}_serializer"
            )

            if serializer_class:
                recipient_data["related_object"] = serializer_class(
                    related_object, context=self.context
                ).data
            else:
                recipient_data["related_object"] = None
        else:
            recipient_data["related_object"] = None
        return recipient_data

    def get_sender(self, instance):
        # Serialize the created_by field as the sender
        if instance.created_by:
            sender_serializer = self.context.get("helixuser_serializer")
            if sender_serializer:
                return sender_serializer(instance.created_by, context=self.context).data
        return None

    class Meta:
        model = SMS
        fields = (
            "id",
            "body",
            "sent_at",
            "recipient",
            "created_by",
            "created_on",
            "sent_at",
            "delivery_status",
            "sender",  # Include sender in the fields
        )


class SMSInboxSerializer(serializers.ModelSerializer):
    recipient = serializers.SerializerMethodField()
    latest_sent_at = serializers.DateTimeField()

    class Meta:
        model = SMSRecipient
        fields = ["recipient", "latest_sent_at"]

    def get_recipient(self, instance):
        recipient_data = {"sent_at": instance["latest_sent_at"]}
        content_type = ContentType.objects.filter(id=instance["content_type"]).first()
        # Include related object data if content_type and object_id exist
        related_object = content_type.get_object_for_this_type(id=instance["object_id"])
        serializer_class = self.context.get(f"{content_type.model}_serializer")

        if serializer_class:
            recipient_data = serializer_class(related_object, context=self.context).data
        return recipient_data


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = "__all__"
