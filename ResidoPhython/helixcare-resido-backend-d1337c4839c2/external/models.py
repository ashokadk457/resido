from django.db import models

from residents.models import Resident
from audit.models import GenericModel

optional = {"null": True, "blank": True}


class CommonwellTask(GenericModel):
    TYPE_CHOICES = (
        ("pending", "Pending"),
        ("complete", "Complete"),
        ("error", "Error"),
    )
    JOB_TYPE = (("doc", "Document fetch"), ("patient", "Patient fetch"))
    PRIORITY = ((1, "High"), (2, "Medium"), (3, "Low"))
    FREQ = ((1, "Once"), (2, "Daily"))
    patient = models.ForeignKey(Resident, on_delete=models.CASCADE)
    state = models.CharField(
        max_length=10, choices=TYPE_CHOICES, **optional, default="pending"
    )
    job_type = models.CharField(
        max_length=10, choices=JOB_TYPE, **optional, default="doc"
    )
    priority = models.IntegerField(default=2, choices=PRIORITY)
    last_refreshed = models.DateTimeField(**optional)
    frequency = models.IntegerField(default=1, choices=FREQ)
    identifier_id = models.CharField(max_length=50, unique=True, **optional)
