import uuid

from audit.models import GenericModel, optional
from django.db import models
from payments.models import Payment
from payments.payment_constants import (
    TransactionEventSource,
    TransactionEvent,
)


class TransactionLog(GenericModel):
    request_id = models.UUIDField(default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Payment, on_delete=models.CASCADE)
    source = models.CharField(
        max_length=100,
        choices=TransactionEventSource.choices(),
        default=TransactionEventSource.SYSTEM.value,
    )
    event = models.CharField(
        max_length=255,
        choices=TransactionEvent.choices(),
    )
    data = models.JSONField()
    call_log = models.JSONField(**optional)

    def __str__(self):
        return f"{self.transaction.display_id}: {self.event}"
