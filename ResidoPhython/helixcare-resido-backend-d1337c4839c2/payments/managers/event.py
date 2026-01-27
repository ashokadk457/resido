from django.utils import timezone
from notifications.apiviews import sendSMS, sendEmail


class ShareManager:
    def trigger_send_email(email, email_recipient):
        response = sendEmail(
            subject=email.subject,
            message=email.body,
            emails=email_recipient.email_address,
            sender_id=str(email.created_by),
            rec_id=str(email.id),
        )
        status_code = response.get("status_code")
        message = response.get("message", {}).get("message")
        if status_code in [200, 201] and message == "Email Sent!":
            for recipient in email.email_recipients.all():
                recipient.delivery_status = "sent"
                recipient.save()
                email.delivery_status = "sent"
                email.sent_at = timezone.now()
                email.save()
        return status_code, message

    def trigger_send_sms(sms, sms_recipient):
        receiving_address = f"{sms_recipient.country_code}{sms_recipient.phone}"
        response = sendSMS(
            to=receiving_address,
            message=sms.body,
            sender_id=str(sms.created_by),
            rec_id=str(sms.id),
        )
        status_code = response.get("status_code")
        error_message = response.get("message", {}).get("error_message")
        if not error_message:
            sms.delivery_status = "sent"
            sms_recipient.delivery_status = "sent"
            sms.sent_at = timezone.now()
            sms.save()
            sms_recipient.save()
        return error_message, status_code
