from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

class GenericModel(models.Model):
    """
    Base model for all other models to inherit from.
    Provides common fields and functionality.
    """

    id = models.UUIDField( db_column='Id',primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class AuditModel(models.Model):
    created_at = models.DateTimeField( db_column='CreatedAt',auto_now_add=True)
    updated_at = models.DateTimeField( db_column='UpdatedAt',auto_now=True)

    class Meta:
        abstract = True

class User(GenericModel,AuditModel):
    first_name = models.TextField(
        db_column='FirstName',
        null=True,
        blank=True
    )

    last_name = models.TextField(
        db_column='LastName',
        null=True,
        blank=True
    )

    email = models.TextField(
        db_column='Email',
        null=True,
        blank=True
    )

    dial_code = models.TextField(
        db_column='DialCode',
        null=True,
        blank=True
    )

    phone_number = models.TextField(
        db_column='PhoneNumber',
        null=True,
        blank=True
    )

    is_phone_verified = models.BooleanField(
        db_column='IsPhoneVerified',
        default=False
    )

    is_email_verified = models.BooleanField(
        db_column='IsEmailVerified',
        default=False
    )

    address_line1 = models.TextField(
        db_column='AddressLine1',
        null=True,
        blank=True
    )

    country_id = models.UUIDField(
        db_column='CountryId',
        null=True,
        blank=True
    )

    state = models.TextField(
        db_column='State',
        null=True,
        blank=True
    )

    city = models.TextField(
        db_column='City',
        null=True,
        blank=True
    )

    zip_code = models.TextField(
        db_column='ZipCode',
        null=True,
        blank=True
    )

    ttlock_username = models.TextField(
        db_column='TTLockUsername',
        null=True,
        blank=True
    )

    ttlock_hash_password = models.TextField(
        db_column='TTLockHashPassword',
        null=True,
        blank=True
    )

    password_hash = models.TextField(
        db_column='PasswordHash',
        null=True,
        blank=True
    )

    password_salt = models.TextField(
        db_column='PasswordSalt',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        db_column='IsActive',
        default=True
    )

    failed_login_attempts = models.IntegerField(
        db_column='FailedLoginAttempts',
        default=0
    )

    last_login = models.DateTimeField(
        db_column='LastLogin',
        null=True,
        blank=True
    )

    is_ekeys_signed_up = models.BooleanField(
        db_column='IsEkeysSingnUp',
        default=False
    )

    user_status = models.IntegerField(
        db_column='UserStatus',
        default=0
    )

    user_type = models.IntegerField(
        db_column='UserType',
        null=True,
        blank=True
    )
    
    def __str__(self):
       return f"{self.__class__} - {self.id} - {self.created_on}"

    class Meta:
        managed = False
        db_table = 'Users'
        

class AccessRefreshToken(GenericModel):
    user_id = models.UUIDField(
        db_column='UserId'
    )

    access_token = models.TextField(
        db_column='AccessToken',
        null=True,
        blank=True
    )

    uid = models.BigIntegerField(
        db_column='Uid',
        null=True,
        blank=True
    )

    expires_in = models.BigIntegerField(
        db_column='ExpiresIn',
        null=True,
        blank=True
    )

    scope = models.TextField(
        db_column='Scope',
        null=True,
        blank=True
    )

    refresh_token = models.TextField(
        db_column='RefreshToken',
        null=True,
        blank=True
    )

    issued_at_utc = models.DateTimeField(
        db_column='IssuedAtUtc',
        null=True,
        blank=True
    )

    def is_expired(self):
        if not self.issued_at_utc or not self.expires_in:
            return False

        expiry = self.issued_at_utc + timedelta(seconds=int(self.expires_in))
        return timezone.now() >= expiry

    class Meta:
        managed = False
        db_table = 'AccessRefreshTokens'

class Key(GenericModel):

    ekey_id = models.IntegerField(
        db_column='EKeyId'
    )

    key_name = models.TextField(
        db_column='KeyName'
    )

    smart_lock_id = models.UUIDField(
        db_column='SmartLockId'
    )

    class Meta:
        managed = False 
        db_table = 'EKeys'