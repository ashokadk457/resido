from django.db import models
from django.contrib.postgres.fields.array import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import uuid

from assets.models import Asset
from common.models import GenericModel, PhoneEmail, optional
from lookup.fields import LookupField
from locations.models import Unit
from residents.models import Resident
from maintenance.constants import MaintenanceStatus
from common.utils.general import (
    get_display_id,
)


class ServiceProvider(GenericModel, PhoneEmail):
    display_id = models.CharField(max_length=100, **optional)
    name = models.CharField(max_length=255)
    profile_image = models.ForeignKey(Asset, on_delete=models.DO_NOTHING, **optional)
    contact_name = models.CharField(max_length=255)
    service_type = LookupField(lookup_name="MAINTENANCE_SERVICE_TYPE", max_length=255)
    languages_known = ArrayField(
        LookupField(max_length=50, lookup_name="LANGUAGE"), default=list, **optional
    )

    description = models.TextField(**optional)
    license_number = models.CharField(max_length=255, **optional)
    registration_info = models.CharField(max_length=500, **optional)

    overall_rating = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    average_rating = models.FloatField(
        default=0.0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    review_count = models.IntegerField(default=0)
    total_jobs = models.IntegerField(default=0)

    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.display_id:
            self.display_id = get_display_id(self, "SERV")
        super(ServiceProvider, self).save(*args, **kwargs)


class ServiceProviderDocument(GenericModel):
    service_provider = models.ForeignKey(
        ServiceProvider, related_name="documents", on_delete=models.CASCADE
    )
    document_type = LookupField(max_length=40, lookup_name="IDENTITY_LIST")
    front_image = models.ForeignKey(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="service_provider_document_front_image",
        **optional,
    )
    back_image = models.ForeignKey(
        Asset,
        on_delete=models.DO_NOTHING,
        related_name="service_provider_document_back_image",
        **optional,
    )
    document_data = models.CharField(max_length=255, **optional)
    is_primary = models.BooleanField(default=False)
    active = models.BooleanField(default=True)


class ServiceProviderReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_provider = models.ForeignKey(
        ServiceProvider, related_name="reviews", on_delete=models.CASCADE
    )
    maintenance = models.ForeignKey(
        "Maintenance",
        related_name="reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    reviewed_by = models.ForeignKey(
        "helixauth.HelixUser",
        related_name="service_provider_reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    rating = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_text = models.TextField(**optional)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        reviewer = self.reviewed_by.get_full_name() if self.reviewed_by else "Anonymous"
        return f"Review for {self.service_provider.name} by {reviewer} - {self.rating} stars"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_service_provider_stats()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self._update_service_provider_stats()

    def _update_service_provider_stats(self):
        """Update the service provider's review statistics."""
        service_provider = self.service_provider
        reviews = service_provider.reviews.all()

        review_count = reviews.count()
        avg_rating = reviews.aggregate(avg_rating=Avg("rating"))["avg_rating"] or 0.0

        service_provider.review_count = review_count
        service_provider.overall_rating = avg_rating
        service_provider.average_rating = avg_rating
        service_provider.save(
            update_fields=["review_count", "overall_rating", "average_rating"]
        )


class Maintenance(GenericModel, PhoneEmail):
    display_id = models.CharField(max_length=100, **optional)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, **optional)
    first_name = models.CharField(max_length=255, **optional)
    middle_name = models.CharField(max_length=255, **optional)
    last_name = models.CharField(max_length=255, **optional)
    service_title = models.CharField(max_length=255)
    service_type = LookupField(lookup_name="MAINTENANCE_SERVICE_TYPE", max_length=255)
    service_priority = LookupField(
        lookup_name="MAINTENANCE_SERVICE_PRIORITY", max_length=255
    )
    reported_date = models.DateField()
    due_date = models.DateField()
    resolved_date = models.DateField(**optional)
    reject_date = models.DateField(**optional)
    reject_reason = LookupField(
        max_length=100, lookup_name="MAINTENANCE_REJECT_REASON", **optional
    )
    reject_notes = models.TextField(**optional)
    description = models.TextField(**optional)
    preferred_contact_method = LookupField(
        lookup_name="COMMUNICATION_MODE", max_length=100, **optional
    )
    recurring_issue = LookupField(
        lookup_name="MAINTENANCE_RECURRING_FREQUENCY", max_length=50, **optional
    )
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, **optional)
    preferred_vendor = models.ForeignKey(
        ServiceProvider,
        on_delete=models.DO_NOTHING,
        related_name="preferred_maintenance_requests",
        **optional,
    )
    assignee = models.ForeignKey(
        ServiceProvider,
        on_delete=models.DO_NOTHING,
        related_name="assigned_maintenance_requests",
        **optional,
    )
    media = models.ManyToManyField(Asset, **optional)
    status = models.CharField(
        choices=MaintenanceStatus.choices(),
        default=MaintenanceStatus.OPEN.value,
        max_length=255,
    )

    def save(self, *args, **kwargs):
        self.display_id = get_display_id(self, "MANT")
        super(Maintenance, self).save(*args, **kwargs)

    class Meta:
        path_to_location = "unit__floor__building"
