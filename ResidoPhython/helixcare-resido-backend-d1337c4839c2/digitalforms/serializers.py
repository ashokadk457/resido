import re
from datetime import datetime
from django.db import transaction
from rest_framework import serializers

from assets.models import Asset
from assets.serializers import AssetSerializer
from staff.models import HelixStaff
from helixauth.models import HelixUser
from common.serializer_mixin import AttributeLevelPermissionMixin
from digitalforms.models import (
    Category,
    ApprovalTeam,
    Form,
    FormVersion,
    FormSection,
    FormRow,
    FormField,
    Widget,
    WidgetField,
    WidgetRow,
    Field,
    FormReview,
    UserResponse,
    UserResponseData,
)
from digitalforms.managers.form_review import FormReviewManager
from digitalforms.constants import FormStatus, FormReviewStatus
from staff.serializers import StaffMinDetailSerializer
from common.errors import ERROR_DETAILS


class FieldSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = "__all__"

    def validate_regex_validator(self, data):
        if data:
            try:
                re.compile(data)
            except Exception:
                raise serializers.ValidationError(
                    detail=ERROR_DETAILS["invalid_data"].format(
                        param="regex_validator"
                    ),
                    code="invalid_data",
                )
        return data

    def validate(self, attrs):
        if self.instance:
            attrs.pop("field_type", None)
        return super().validate(attrs)


class WidgetSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = "__all__"


class WidgetRowSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    widget_id = serializers.PrimaryKeyRelatedField(
        queryset=Widget.objects.all(),
        required=True,
        write_only=True,
        source="widget",
    )

    class Meta:
        model = WidgetRow
        fields = "__all__"
        read_only_fields = [
            "widget",
        ]


class WidgetFieldSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    row_id = serializers.PrimaryKeyRelatedField(
        queryset=WidgetRow.objects.all(),
        required=True,
        write_only=True,
        source="row",
    )
    field_id = serializers.PrimaryKeyRelatedField(
        queryset=Field.objects.all(),
        required=True,
        write_only=True,
        source="field",
    )

    class Meta:
        model = WidgetField
        fields = "__all__"
        read_only_fields = ["row", "field"]


class CategorySerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ApprovalTeamSerializer(
    AttributeLevelPermissionMixin, serializers.ModelSerializer
):
    staff_id = serializers.PrimaryKeyRelatedField(
        queryset=HelixStaff.objects.all(),
        required=True,
        write_only=True,
        source="staff",
    )
    staff = StaffMinDetailSerializer(read_only=True)

    class Meta:
        model = ApprovalTeam
        fields = "__all__"
        read_only_fields = ("name",)

    def create(self, validated_data):
        validated_data["name"] = validated_data.get("staff").name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("staff"):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["field_update_not_allowed"].format(param="staff"),
                code="field_update_not_allowed",
            )
        return super().update(instance, validated_data)


class FormVersionSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = FormVersion
        fields = "__all__"

    def validate(self, attrs):
        if (
            attrs.get("approval_due_date")
            and attrs.get("approval_due_date") < datetime.now().date()
        ):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["invalid_data"].format(param="approval_due_date"),
                code="invalid_data",
            )
        return super().validate(attrs)

    def update(self, instance, validated_data):
        refresh_reviews, start_review = False, False
        if new_status := validated_data.get("status"):
            current_status = instance.status
            if (
                new_status == FormStatus.draft.value
                and current_status == FormStatus.approved.value
            ):
                raise serializers.ValidationError(
                    detail=ERROR_DETAILS["update_not_allowed"].format(param="status"),
                    code="update_not_allowed",
                )
            if (
                new_status == FormStatus.draft.value
                and current_status == FormStatus.in_review.value
            ):
                refresh_reviews = True
            if (
                new_status == FormStatus.approved.value
                and current_status == FormStatus.in_review.value
            ):
                count_of_required_reviews = FormReview.objects.filter(
                    form_version=instance, active=True, approval_required=True
                ).count()
                count_of_req_approved_reviews = FormReview.objects.filter(
                    form_version=instance,
                    active=True,
                    approval_required=True,
                    status=FormReviewStatus.approved.value,
                ).count()
                if count_of_req_approved_reviews != count_of_required_reviews:
                    raise serializers.ValidationError(
                        detail=ERROR_DETAILS["update_not_allowed"].format(
                            param="status"
                        )
                        + ", All required reviewers have not yet approved the form.",
                        code="update_not_allowed",
                    )
            if (
                new_status == FormStatus.in_review.value
                and current_status == FormStatus.draft.value
            ):
                if not instance.approval_due_date and not validated_data.get(
                    "approval_due_date"
                ):
                    raise serializers.ValidationError(
                        detail=ERROR_DETAILS["update_not_allowed"].format(
                            param="status"
                        )
                        + ", Please add approval due date first.",
                        code="update_not_allowed",
                    )
                if (
                    FormReview.objects.filter(
                        form_version=instance, active=True
                    ).count()
                    == 0
                ):
                    raise serializers.ValidationError(
                        detail=ERROR_DETAILS["update_not_allowed"].format(
                            param="status"
                        )
                        + ", Please add atleast 1 reviewer to the form",
                        code="update_not_allowed",
                    )
                start_review = True
        if (
            validated_data.get("sequential_approval")
            and not instance.sequential_approval
        ):
            if (
                FormReview.objects.filter(
                    form_version=instance, active=True, sequence_number=None
                ).count()
                > 0
            ):
                raise serializers.ValidationError(
                    detail=ERROR_DETAILS["update_not_allowed"].format(param="status")
                    + ", Please add sequence number to the reviewers first",
                    code="update_not_allowed",
                )
        if (
            validated_data.get("all_approval_required")
            and not instance.all_approval_required
        ):
            FormReview.objects.filter(
                form_version=instance, active=True, approval_required=False
            ).update(approval_required=True)
        resp = super().update(instance, validated_data)
        if refresh_reviews:
            existing_reviewers = FormReview.objects.filter(
                form_version=instance, active=True
            )
            existing_reviewers.update(active=False)
            for i in existing_reviewers:
                i.id = None
                i.active = True
                i.save()
        if start_review or refresh_reviews:
            FormReviewManager.trigger_review_notification(form_version=instance)
        return resp


class FormListSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    versions = FormVersionSerializer(read_only=True, many=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Form
        fields = "__all__"


class FormCreateSerializer(AttributeLevelPermissionMixin, serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        write_only=True,
        source="category",
    )
    header_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        required=False,
        write_only=True,
        source="header",
    )
    pdf_file_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        required=False,
        write_only=True,
        source="pdf_file",
    )
    versions = FormVersionSerializer(read_only=True, many=True)
    category = CategorySerializer(read_only=True)
    header = AssetSerializer(read_only=True)
    pdf_file = AssetSerializer(read_only=True)

    class Meta:
        model = Form
        fields = "__all__"

    def validate(self, attrs):
        if (
            attrs.get("end_date")
            and attrs.get("start_date")
            and attrs.get("start_date") > attrs.get("end_date")
        ):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["invalid_end_date"], code="invalid_end_date"
            )
        if attrs.get("form_type") == "file_upload" and not attrs.get("pdf_file"):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["missing_required_param"].format(param="pdf_file"),
                code="missing_required_param",
            )
        return super().validate(attrs)

    def create(self, validated_data):
        instance = super().create(validated_data)
        FormVersion.objects.create(form=instance, version_number=1)
        return instance


class FormVersionSerializerMixin:
    @staticmethod
    def can_update_form_version(form_version, entity):
        if form_version.status == FormStatus.approved.value:
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["update_not_allowed"].format(param=entity),
                code="update_not_allowed",
            )
        return True


class FormSectionSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    form_version_id = serializers.PrimaryKeyRelatedField(
        queryset=FormVersion.objects.all(),
        required=True,
        write_only=True,
        source="form_version",
    )
    widget_id = serializers.PrimaryKeyRelatedField(
        queryset=Widget.objects.all(),
        required=False,
        write_only=True,
        source="widget",
    )

    class Meta:
        model = FormSection
        fields = "__all__"
        read_only_fields = ["form_version", "widget"]

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.form_version, entity="section"
            )
        return super().validate(attrs)


class FormRowSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=FormSection.objects.all(),
        required=True,
        write_only=True,
        source="section",
    )

    class Meta:
        model = FormRow
        fields = "__all__"
        read_only_fields = [
            "section",
        ]

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.section.form_version, entity="row"
            )
        return super().validate(attrs)


class FormFieldSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    row_id = serializers.PrimaryKeyRelatedField(
        queryset=FormRow.objects.all(),
        required=True,
        write_only=True,
        source="row",
    )
    field_id = serializers.PrimaryKeyRelatedField(
        queryset=Field.objects.all(),
        required=True,
        write_only=True,
        source="field",
    )

    class Meta:
        model = FormField
        fields = "__all__"
        read_only_fields = ["row", "field"]

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.row.section.form_version, entity="row"
            )
        return super().validate(attrs)


class FormFieldDetailSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    field = FieldSerializer(read_only=True)

    class Meta:
        model = FormField
        fields = "__all__"

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.row.section.form_version, entity="row"
            )
        return super().validate(attrs)


class FormRowDetailSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    fields = FormFieldDetailSerializer(source="form_fields", many=True, read_only=True)

    class Meta:
        model = FormRow
        fields = "__all__"

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.section.form_version, entity="row"
            )
        return super().validate(attrs)


class FormSectionDetailSerializer(
    AttributeLevelPermissionMixin,
    FormVersionSerializerMixin,
    serializers.ModelSerializer,
):
    rows = FormRowDetailSerializer(source="form_rows", many=True, read_only=True)

    class Meta:
        model = FormSection
        fields = "__all__"
        read_only_fields = ["form_version", "widget"]

    def validate(self, attrs):
        if self.instance:
            self.can_update_form_version(
                form_version=self.instance.form_version, entity="section"
            )
        return super().validate(attrs)


class FormReviewSerializer(
    AttributeLevelPermissionMixin,
    serializers.ModelSerializer,
):
    form_version_id = serializers.PrimaryKeyRelatedField(
        queryset=FormVersion.objects.all(),
        required=True,
        write_only=True,
        source="form_version",
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=ApprovalTeam.objects.all().filter(active=True),
        required=True,
        write_only=True,
        source="reviewer",
    )

    class Meta:
        model = FormReview
        fields = "__all__"
        read_only_fields = [
            "form_version",
            "reviewer",
        ]

    def validate(self, attrs):
        if self.instance:
            attrs.pop("form_version", None)
            attrs.pop("reviewer", None)
            form_version = self.instance.form_version
        else:
            form_version = attrs.get("form_version")
        status = (
            attrs.get("status")
            if attrs.get("status")
            else (
                self.instance.status
                if self.instance
                else FormReviewStatus.pending.value
            )
        )
        if status == FormReviewStatus.approved.value:
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["update_not_allowed"].format(param="status"),
                code="update_not_allowed",
            )
        if form_version.sequential_approval and not attrs.get("sequence_number"):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["missing_required_param"].format(
                    param="sequence_number"
                ),
                code="missing_required_param",
            )
        if form_version.sequential_approval and attrs.get("sequence_number"):
            try:
                FormReview.objects.get(
                    form_version=form_version,
                    sequence_number=attrs.get("sequence_number"),
                    active=True,
                )
                raise serializers.ValidationError(
                    detail=ERROR_DETAILS["record_already_exists"].format(
                        param="sequence_number"
                    ),
                    code="record_already_exists",
                )
            except Exception:
                pass
        return super().validate(attrs)

    @staticmethod
    def _post_create_update_trigger(instance, old_status):
        if instance.status != old_status:
            if instance.status == FormReviewStatus.approved.value:
                FormReviewManager.on_approved_review_submission(
                    form_version=instance.form_version
                )
            elif instance.status == FormReviewStatus.rejected.value:
                FormReviewManager.on_rejected_review_submission(
                    form_version=instance.form_version,
                )

    def create(self, validated_data):
        old_status = validated_data.get("status", FormReviewStatus.pending.value)
        instance = super().create(validated_data)
        self._post_create_update_trigger(instance=instance, old_status=old_status)
        return instance

    def update(self, instance, validated_data):
        old_status = validated_data.get("status", instance.status)
        instance = super().update(instance, validated_data)
        self._post_create_update_trigger(instance=instance, old_status=old_status)
        return instance


class UserResponseDataSerializer(
    AttributeLevelPermissionMixin, serializers.ModelSerializer
):
    response_id = serializers.PrimaryKeyRelatedField(
        queryset=UserResponse.objects.all(),
        required=False,
        write_only=True,
        source="response",
    )
    form_field_id = serializers.PrimaryKeyRelatedField(
        queryset=FormField.objects.all(),
        required=True,
        write_only=True,
        source="form_field",
    )
    file_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        required=False,
        write_only=True,
        source="file",
    )

    def validate(self, attrs):
        if not attrs.get("text") and not attrs.get("file"):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["anyone_required"],
                code="anyone_required",
            )
        return super().validate(attrs)

    class Meta:
        model = UserResponseData
        fields = "__all__"
        read_only_fields = (
            "form_field",
            "response",
            "file",
        )


class UserResponseSerializer(
    AttributeLevelPermissionMixin,
    serializers.ModelSerializer,
):
    data = UserResponseDataSerializer(many=True, required=True)
    form_version_id = serializers.PrimaryKeyRelatedField(
        queryset=FormVersion.objects.all(),
        required=True,
        write_only=True,
        source="form_version",
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=HelixUser.objects.all(),
        required=True,
        write_only=True,
        source="user",
    )

    class Meta:
        model = UserResponse
        fields = "__all__"
        read_only_fields = (
            "form_version",
            "user",
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("form_version", None)
        validated_data.pop("data", [])
        resp_data = self.initial_data.get("data", [])
        self._pre_save(
            resp_data=resp_data,
            validated_data=validated_data,
            form_version=instance.form_version,
            instance_id=instance.id,
        )
        resp = super().update(instance, validated_data)
        self._post_save(instance=instance, resp_data=resp_data)
        return resp

    @staticmethod
    def _pre_save(resp_data, validated_data, form_version, instance_id=None):
        user = validated_data.get("user")
        if (
            UserResponse.objects.filter(
                user=user, form_version=form_version, active=True
            ).count()
            > 0
        ):
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["record_already_exists"].format(
                    param="form_version"
                ),
                code="record_already_exists",
            )
        form_field_ids = [x.get("form_field_id") for x in resp_data]
        field_objs = FormField.objects.filter(
            id__in=form_field_ids,
            row__section__form_version=form_version,
        )
        req_fields_count = FormField.objects.filter(
            row__section__form_version=form_version, required=True
        ).count()
        if req_fields_count != field_objs.filter(required=True).count():
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["required_fields_missing"],
                code="required_fields_missing",
            )
        actual_field_ids = list(field_objs.values_list("id", flat=True))
        if len(list(set(actual_field_ids) - set(form_field_ids))) > 0:
            raise serializers.ValidationError(
                detail=ERROR_DETAILS["invalid_field_ids"],
                code="invalid_field_ids",
            )
        if instance_id:
            UserResponseData.objects.filter(
                user=user,
                form_version=form_version,
            ).delete()

    @staticmethod
    def _post_save(instance, resp_data):
        for x in resp_data:
            x["response_id"] = instance.id
            srz = UserResponseDataSerializer(data=x)
            srz.is_valid(raise_exception=True)
            srz.save()

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("data", [])
        form_version = validated_data.get("form_version")
        resp_data = self.initial_data.get("data", [])
        self._pre_save(
            resp_data=resp_data,
            validated_data=validated_data,
            form_version=form_version,
        )
        instance = super().create(validated_data)
        self._post_save(instance=instance, resp_data=resp_data)
        return instance
