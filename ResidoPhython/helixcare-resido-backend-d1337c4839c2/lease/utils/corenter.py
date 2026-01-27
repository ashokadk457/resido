import traceback

from hb_core.utils.logging import logger
from helixauth.models import HelixUser
from helixauth.serializers import HelixUserSerializer
from residents.constants import ResidentProfileType
from residents.managers.patient import ResidentManager
from residents.models import Resident


def create_corenter_accounts(additional_holders, context=None):
    """
    Create Resident accounts for co-renters/additional lease holders
    and send password setup emails to them.

    Args:
        additional_holders: QuerySet or list of ApplicationAdditionalLeaseHolders objects
        context: Optional serializer context for HelixUserSerializer
    """
    logger.info(
        f"create_corenter_accounts called with {len(additional_holders)} holders"
    )

    for holder in additional_holders:
        email = holder.email
        name = holder.name

        if not email:
            logger.warning(f"Skipping co-renter with no email: {name}")
            continue

        try:
            # Parse name into first_name and last_name
            name_parts = name.strip().split(" ", 1) if name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            if not first_name:
                first_name = "Co-Renter"
            if not last_name:
                last_name = "User"  # HelixUserSerializer requires non-empty last_name

            # Check if user with this email already exists
            existing_user = HelixUser.objects.filter(email__iexact=email).first()

            if existing_user:
                # Check if resident exists for this user
                existing_resident = Resident.objects.filter(user=existing_user).first()
                if existing_resident:
                    # Co-renter already has an account, skip
                    logger.info(
                        f"Co-renter with email {email} already has a resident account"
                    )
                    continue

                # User exists but no resident - create resident for existing user
                logger.info(f"Creating resident for existing user {email}")
                resident = Resident.objects.create(
                    user=existing_user,
                    profile_type=ResidentProfileType.TENANT.value,
                    resident_id=ResidentManager.generate_resident_id(
                        existing_user.first_name or first_name,
                        existing_user.last_name or last_name,
                    ),
                )
                # Send password setup email
                ResidentManager.send_email(resident)
                logger.info(f"Created resident for existing user {email}")
                continue

            # Create new HelixUser
            user_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
            }
            logger.info(f"Creating new co-renter user: {user_data}")
            user_serializer = HelixUserSerializer(data=user_data, context=context or {})
            if not user_serializer.is_valid():
                logger.error(
                    f"Validation errors for co-renter {email}: {user_serializer.errors}"
                )
                continue
            user = user_serializer.save()

            # Create Resident
            resident = Resident.objects.create(
                user=user,
                profile_type=ResidentProfileType.TENANT.value,
                resident_id=ResidentManager.generate_resident_id(first_name, last_name),
            )

            # Send password setup email
            ResidentManager.send_email(resident)

            logger.info(f"Created co-renter account for {email}")

        except Exception as e:
            logger.error(f"Error creating co-renter account for {email}: {e}")
            logger.error(traceback.format_exc())
