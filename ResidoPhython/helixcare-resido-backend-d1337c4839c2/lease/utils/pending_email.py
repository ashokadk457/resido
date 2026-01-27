from common.utils.logging import logger
from lease.managers.application import ApplicationManager
from lease.models import Application
from residents.models import Resident


def send_pending_application_emails(user_or_resident):
    """
    Check if there's a pending application for this resident and send
    the application form email after password setup.

    Args:
        user_or_resident: Either a HelixUser instance or a Resident instance.
                         If HelixUser is passed, the associated Resident will be looked up.
    """
    try:
        # Determine if we received a Resident or HelixUser
        if isinstance(user_or_resident, Resident):
            resident = user_or_resident
        else:
            # Assume it's a HelixUser, find the associated resident
            resident = Resident.objects.filter(user=user_or_resident).first()

        if not resident:
            return

        # Find pending applications that need email sent
        pending_applications = Application.objects.filter(
            resident=resident, pending_activation_email=True
        )

        for application in pending_applications:
            # Send the application form email
            mngr = ApplicationManager(instance=application)
            mngr.send_email()

            # Mark as email sent
            application.pending_activation_email = False
            application.save(update_fields=["pending_activation_email"])

    except Exception as e:
        # Log the error but don't fail the password reset
        logger.error(f"Error sending pending application email: {e}")
