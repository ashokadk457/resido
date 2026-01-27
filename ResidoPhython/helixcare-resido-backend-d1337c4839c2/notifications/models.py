from uuid import uuid4

from django.db import models
from audit.models import GenericModel
from locations.models import Location, Property
from lookup.fields import LookupField
from residents.models import Resident
from staff.models import HelixStaff
from django.contrib.postgres.fields.array import ArrayField
from django.utils.deconstruct import deconstructible
import os

from assets.models import Asset

# Create your models here.
optional = {"null": True, "blank": True}


@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        # get filename
        if instance.pk:
            filename = "{}.{}".format(filename.split(".")[0] + str(instance.pk), ext)
        else:
            # set filename as random string
            filename = "{}.{}".format(filename.split(".")[0] + str(uuid4().hex), ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


class NotificationSetting(GenericModel):
    WHEN = (("1", "ASAP"), ("2", "Specified Time"))
    notification_type = LookupField(
        max_length=200, lookup_name="COMMUNICATION_MODE", **optional
    )
    frequency = models.IntegerField(default=1)
    language = LookupField(max_length=200, lookup_name="LANGUAGE", **optional)
    event_type = LookupField(max_length=200, lookup_name="EVENT_TYPE", **optional)
    when = models.CharField(choices=WHEN, default="1", max_length=100)
    send_time = models.JSONField(default=list)
    message = models.TextField()


class NotificationTypePriority(GenericModel):
    event_type = LookupField(max_length=200, lookup_name="EVENT_TYPE", **optional)
    notification_type = ArrayField(
        LookupField(max_length=200, lookup_name="COMMUNICATION_MODE", **optional),
        default=list,
    )


class NotificationQueue(GenericModel):
    NOTIFICATION_PRIORITY = (
        (1, "High"),
        (2, "Medium"),
        (3, "Low"),
    )
    STATUS = ((1, "Sent"), (2, "Failed"), (3, "Pending"), (4, "Viewed"))
    notes = models.TextField(**optional)
    status = models.IntegerField(choices=STATUS, default=3)
    priority = models.IntegerField(choices=NOTIFICATION_PRIORITY, default=2)
    payload = models.JSONField(default=list)
    sent_date = models.DateTimeField(**optional)
    received_date = models.DateTimeField(**optional)
    error_code = models.CharField(**optional, max_length=100)
    user = models.ForeignKey(
        Resident, related_name="User", on_delete=models.CASCADE, **optional
    )
    provider = models.ForeignKey(
        HelixStaff, related_name="User", on_delete=models.CASCADE, **optional
    )
    receiving_address = models.CharField(max_length=255, **optional)
    notification_setting = models.ForeignKey(
        NotificationSetting, on_delete=models.CASCADE
    )


class NotificationDL(GenericModel):
    STATUS = ((1, "Active"), (2, "Inactive"), (3, "Pending"), (4, "Reviewed"))
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20)
    contact_cnt = models.IntegerField(default=0)
    status = models.IntegerField(choices=STATUS, default=3)
    healthcenter = models.ForeignKey(
        Property, **optional, related_name="dl_healthcenter", on_delete=models.CASCADE
    )
    facility = models.ForeignKey(
        Location, **optional, related_name="dl_facility", on_delete=models.CASCADE
    )
    alt_name = models.CharField(max_length=100, **optional)
    desc = models.TextField(**optional)
    frequency = models.CharField(max_length=10)
    count = models.IntegerField(default=0)


class NotificationDLFile(GenericModel):
    STATUS = ((1, "Completed"), (2, "In Progress"), (3, "Pending"), (4, "Errored"))
    file = models.ForeignKey(Asset, on_delete=models.DO_NOTHING)
    file_name = models.CharField(max_length=100, **optional)
    status = models.IntegerField(choices=STATUS, default=3)
    records_inserted = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_errored = models.IntegerField(default=0)
    file_type = models.CharField(max_length=100, **optional)


class NotificationUserDL(GenericModel):
    STATUS = ((1, "Active"), (2, "Inactive"), (3, "Pending"), (4, "Reviewed"))
    status = models.IntegerField(choices=STATUS, default=3)
    dl = models.ForeignKey(NotificationDL, on_delete=models.CASCADE)
    user = models.ForeignKey(Resident, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self._state.adding:
            count = NotificationUserDL.objects.filter(dl=self.dl).count()
            count = count + 1
        else:
            count = NotificationUserDL.objects.filter(dl=self.dl).count()
        dl = NotificationDL.objects.filter(id=str(self.dl.id)).first()
        dl.contact_cnt = count
        dl.save()
        super(NotificationUserDL, self).save(*args, **kwargs)


class NotificationTemplate(GenericModel):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    language = models.CharField(max_length=10, **optional)


class NotificationMessage(GenericModel):
    STATUS = ((1, "Email"), (2, "SMS"), (3, "Both"))
    healthcenter = models.ForeignKey(
        Property, **optional, related_name="tem_healthcenter", on_delete=models.CASCADE
    )
    facility = models.ForeignKey(
        Location, **optional, related_name="tem_facility", on_delete=models.CASCADE
    )
    dl = models.ForeignKey(NotificationDL, on_delete=models.CASCADE, **optional)
    contacts = models.ManyToManyField(Resident, related_name="contacts_msg", **optional)
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.CASCADE, **optional
    )
    frequency = models.CharField(max_length=10)
    send_msg = models.IntegerField(choices=STATUS, default=3)
    subject = models.CharField(max_length=100, **optional)
    message = models.TextField(**optional)
