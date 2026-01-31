import uuid
from django.db import models

class Key(models.Model):
    id = models.UUIDField(
        primary_key=True,
        db_column='Id'
    )

    ekey_id = models.IntegerField(
        db_column='EKeyId'
    )

    key_name = models.TextField(
        db_column='KeyName'
    )

    smart_lock_id = models.UUIDField(
        db_column='SmartLockId'
    )

    created_at = models.DateTimeField(
        db_column='CreatedAt'
    )

    updated_at = models.DateTimeField(
        db_column='UpdatedAt'
    )

    class Meta:
        managed = False 
        db_table = 'EKeys'
