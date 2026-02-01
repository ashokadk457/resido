import uuid
from django.db import models

class AccessRefreshToken(models.Model):
    id = models.UUIDField(
        primary_key=True,
        db_column='Id'
    )

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

    class Meta:
        managed = False
        db_table = 'AccessRefreshTokens'