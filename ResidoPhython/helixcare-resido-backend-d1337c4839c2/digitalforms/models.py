from django.db import models
from django.contrib.postgres.fields import ArrayField
from assets.models import Asset
from audit.models import GenericModel, NameActiveGenericModel, optional
from helixauth.models import HelixUser
from staff.models import HelixStaff
from digitalforms.constants import FieldType, FormType, FormReviewStatus, FormStatus


class Category(NameActiveGenericModel):
    def __str__(self):
        return self.name


class ApprovalTeam(NameActiveGenericModel):
    staff = models.ForeignKey(HelixStaff, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Field(GenericModel):
    field_type = models.CharField(
        choices=FieldType.choices(), max_length=255, unique=True
    )
    regex_validator = models.TextField(**optional)
    default_value = models.TextField(**optional)
    default_choices = ArrayField(models.CharField(max_length=255), **optional)
    placeholder = models.CharField(max_length=255, **optional)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.field_type


class Widget(NameActiveGenericModel):
    pass


class WidgetRow(GenericModel):
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)
    position = models.IntegerField()

    class Meta:
        unique_together = (("widget", "position"),)


class GenericFormField(GenericModel):
    label = models.CharField(max_length=255)
    position = models.IntegerField()
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    default_value = models.TextField(**optional)
    default_choices = ArrayField(models.CharField(max_length=255), **optional)
    placeholder = models.CharField(max_length=255, **optional)
    regex_validator = models.TextField(**optional)
    # position identifier in manual form
    column = models.IntegerField(default=1, choices=((1, 1), (2, 2)), **optional)
    length = models.IntegerField(default=1, choices=((1, 1), (2, 2)), **optional)
    # position identifier in PDF upload
    x_cordinate = models.FloatField(**optional)
    y_cordinate = models.FloatField(**optional)
    width = models.FloatField(**optional)
    height = models.FloatField(**optional)
    # other general properties
    required = models.BooleanField(default=True)
    read_only = models.BooleanField(default=True)
    hidden = models.BooleanField(default=True)

    class Meta:
        abstract = True


class WidgetField(GenericFormField):
    row = models.ForeignKey(WidgetRow, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("row", "position"),)


class Form(NameActiveGenericModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    header = models.ForeignKey(
        Asset, on_delete=models.PROTECT, related_name="form_header", **optional
    )
    form_type = models.CharField(choices=FormType.choices(), max_length=200)
    pdf_file = models.ForeignKey(
        Asset, on_delete=models.PROTECT, related_name="form_pdf_file", **optional
    )
    start_date = models.DateField()
    end_date = models.DateField()


class FormVersion(GenericModel):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField(default=1)
    status = models.CharField(
        choices=FormStatus.choices(), max_length=255, default="draft"
    )
    approval_due_date = models.DateField(**optional)
    all_approval_required = models.BooleanField(default=True)
    auto_approval = models.BooleanField(default=False)
    sequential_approval = models.BooleanField(default=False)

    class Meta:
        unique_together = (("form", "version_number"),)


class FormSection(GenericModel):
    form_version = models.ForeignKey(FormVersion, on_delete=models.CASCADE)
    heading = models.CharField(max_length=255)
    position = models.IntegerField()
    widget = models.ForeignKey(Widget, on_delete=models.PROTECT, **optional)

    class Meta:
        unique_together = (("form_version", "position"),)


class FormRow(GenericModel):
    section = models.ForeignKey(
        FormSection, on_delete=models.CASCADE, related_name="form_rows"
    )
    position = models.IntegerField()

    class Meta:
        unique_together = (("section", "position"),)


class FormField(GenericFormField):
    row = models.ForeignKey(
        FormRow, on_delete=models.CASCADE, related_name="form_fields"
    )

    class Meta:
        unique_together = (("row", "position"),)


class FormReview(GenericModel):
    form_version = models.ForeignKey(FormVersion, on_delete=models.CASCADE)
    sequence_number = models.IntegerField(**optional)
    reviewer = models.ForeignKey(ApprovalTeam, on_delete=models.PROTECT)
    status = models.CharField(max_length=100, choices=FormReviewStatus.choices())
    comment = models.TextField(**optional)
    approval_required = models.BooleanField(default=True)
    active = models.BooleanField(default=True)


class UserResponse(GenericModel):
    user = models.ForeignKey(HelixUser, on_delete=models.CASCADE)
    form_version = models.ForeignKey(FormVersion, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    class Meta:
        path_to_resident_id = "user__resident__id"


class UserResponseData(GenericModel):
    response = models.ForeignKey(
        UserResponse, on_delete=models.CASCADE, related_name="data"
    )
    form_field = models.ForeignKey(FormField, on_delete=models.CASCADE)
    text = models.TextField(**optional)
    file = models.ForeignKey(Asset, on_delete=models.PROTECT, **optional)
