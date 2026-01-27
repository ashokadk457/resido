from django.contrib.contenttypes.models import ContentType
from connecthub.models import SMS, Email, SMSRecipient, EmailRecipient
from payments.managers import event


class SMSManager:
    share_manager = event.ShareManager

    def build_sms_recipient(self, sms, phone_number, country_code, patient_obj):
        content_type = ContentType.objects.filter(model="patient").first()
        sms_recipient = SMSRecipient.objects.create(
            sms=sms,
            country_code=country_code,
            phone=phone_number,
            content_type=content_type,
            object_id=patient_obj,
        )
        return self.share_manager.trigger_send_sms(sms, sms_recipient)

    def build_sms(
        self,
        body,
        created_by,
        phone_number,
        country_code,
        patient_obj,
        parent_sms=None,
        sent_at=None,
        recipients=None,
    ):
        sms = SMS.objects.create(
            body=body, created_by=created_by, parent_sms=parent_sms, sent_at=sent_at
        )
        if recipients:
            sms.recipients.set(recipients)
        return self.build_sms_recipient(sms, phone_number, country_code, patient_obj)


class EmailManager:
    share_manager = event.ShareManager

    def build_email_recipient(self, email, receiving_address):
        email_recipient = EmailRecipient.objects.create(
            email=email,
            email_address=receiving_address,
            recipient_type="to",
        )
        return self.share_manager.trigger_send_email(email, email_recipient)

    def build_email(
        self,
        subject,
        body,
        created_by,
        receiving_address,
        recipients=None,
        attachments=None,
        is_archive=False,
        sent_at=None,
        is_draft=False,
    ):
        email = Email.objects.create(
            subject=subject,
            body=body,
            created_by=created_by,
            parent_email=None,
            is_draft=is_draft,
            is_archive=is_archive,
            sent_at=sent_at,
        )
        if attachments:
            email.attchments.set(attachments)
        if recipients:
            email.recipients.set(recipients)
        return self.build_email_recipient(email, receiving_address)
