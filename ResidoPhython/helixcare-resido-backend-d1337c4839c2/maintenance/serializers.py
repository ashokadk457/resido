from datetime import datetime

from common.serializers import BaseSerializer, serializers
from common.errors import ERROR_DETAILS
from common.validators import validate_country_code, validate_phone_number
from assets.models import Asset
from assets.serializers import AssetSerializer
from locations.models import Unit
from locations.serializers import UnitDetailSerializer
from residents.models import Resident
from residents.serializers import ResidentSerializer
from helixauth.models import HelixUser
from helixauth.serializers import HelixPartialUserSerializer
from maintenance.models import (
    ServiceProvider,
    ServiceProviderDocument,
    ServiceProviderReview,
    Maintenance,
)
from maintenance.constants import MaintenanceStatus


class ServiceProviderDocumentSerializer(BaseSerializer):
    service_provider = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        required=False,
    )
    front_image = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        required=False,
    )
    back_image = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        required=False,
    )

    front_image_details = AssetSerializer(
        read_only=True, required=False, source="front_image"
    )
    back_image_details = AssetSerializer(
        read_only=True, required=False, source="back_image"
    )

    class Meta:
        model = ServiceProviderDocument
        fields = (
            "id",
            "service_provider",
            "document_type",
            "front_image",
            "front_image_details",
            "back_image",
            "back_image_details",
            "document_data",
            "is_primary",
            "active",
            "created_on",
            "updated_on",
        )


class ServiceProviderSerializer(BaseSerializer):
    profile_image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="profile_image",
        required=False,
    )
    profile_image = AssetSerializer(read_only=True)
    documents = ServiceProviderDocumentSerializer(
        many=True,
        write_only=True,
        required=False,
    )
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    work_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    home_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    fax = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )

    class Meta:
        model = ServiceProvider
        fields = "__all__"

    def validate_work_country_code(self, value):
        if value:
            validate_country_code(value)
        return value

    def validate_phone_country_code(self, value):
        if value:
            validate_country_code(value)
        return value

    def validate_home_phone_country_code(self, value):
        if value:
            validate_country_code(value)
        return value

    def validate_fax_country_code(self, value):
        if value:
            validate_country_code(value)
        return value

    def validate(self, attrs):
        instance = self.instance
        fields = [
            "name",
            "service_type",
            "email",
            "phone",
            "home_phone",
            "work_phone",
            "contact_name",
        ]
        values = {
            field: attrs.get(field) or (getattr(instance, field) if instance else None)
            for field in fields
        }

        if not instance:
            required = ["name", "service_type", "contact_name", "email", "phone"]
            for field in required:
                if not values[field]:
                    raise serializers.ValidationError(
                        {field: "This field is required."}
                    )

        qs = ServiceProvider.objects.filter(
            **{
                "service_type": values["service_type"],
                "name__iexact": values["name"],
                "email__iexact": values["email"],
                "phone__iexact": values["phone"],
                "home_phone__iexact": values["home_phone"],
                "work_phone__iexact": values["work_phone"],
                "contact_name__iexact": values["contact_name"],
            }
        )

        if instance:
            qs = qs.exclude(id=instance.id)

        if qs.exists():
            raise serializers.ValidationError(
                code="duplicate_service_details",
                detail=ERROR_DETAILS["duplicate_service_details"],
            )

        return attrs

    def create(self, validated_data):
        documents_data = validated_data.pop("documents", [])
        service_provider = super().create(validated_data)

        # Create documents for the service provider
        for document_data in documents_data:
            document_data["service_provider"] = service_provider
            ServiceProviderDocument.objects.create(**document_data)

        return service_provider

    def update(self, instance, validated_data):
        documents_data = validated_data.pop("documents", None)
        service_provider = super().update(instance, validated_data)

        # Update/create documents for the service provider
        if documents_data is not None:
            # Option 1: Replace all documents with new ones
            # Uncomment the line below to delete existing documents when updating
            # service_provider.documents.all().delete()

            # Option 2: Update existing and create new documents
            existing_doc_ids = {doc["id"] for doc in documents_data if "id" in doc}
            service_provider.documents.exclude(id__in=existing_doc_ids).delete()

            for document_data in documents_data:
                doc_id = document_data.pop("id", None)
                if doc_id:
                    ServiceProviderDocument.objects.filter(id=doc_id).update(
                        **document_data
                    )
                else:
                    document_data["service_provider"] = service_provider
                    ServiceProviderDocument.objects.create(**document_data)

        return service_provider


class ServiceProviderReviewListSerializer(BaseSerializer):
    reviewed_by = HelixPartialUserSerializer(read_only=True)

    class Meta:
        model = ServiceProviderReview
        fields = "__all__"


class ServiceProviderReviewSerializer(BaseSerializer):
    service_provider_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        write_only=True,
        source="service_provider",
    )
    maintenance_id = serializers.PrimaryKeyRelatedField(
        queryset=Maintenance.objects.all(),
        write_only=True,
        source="maintenance",
        required=False,
        allow_null=True,
    )
    reviewed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=HelixUser.objects.all(),
        write_only=True,
        source="reviewed_by",
        required=False,
        allow_null=True,
    )
    reviewed_by = HelixPartialUserSerializer(read_only=True)

    class Meta:
        model = ServiceProviderReview
        fields = (
            "id",
            "service_provider_id",
            "maintenance_id",
            "reviewed_by_id",
            "reviewed_by",
            "rating",
            "review_text",
            "created_on",
            "updated_on",
        )

    def create(self, validated_data):
        if not validated_data.get("reviewed_by"):
            request = self.context.get("request")
            if request and hasattr(request, "user") and request.user.is_authenticated:
                validated_data["reviewed_by"] = request.user

        return super().create(validated_data)


class MaintenanceDetailsForReviewSerializer(BaseSerializer):
    class Meta:
        model = Maintenance
        fields = ("id", "display_id", "service_title", "service_type")


class ServiceProviderReviewDetailSerializer(BaseSerializer):
    maintenance_details = MaintenanceDetailsForReviewSerializer(
        source="maintenance", read_only=True, required=False
    )
    reviewed_by = HelixPartialUserSerializer(read_only=True)

    class Meta:
        model = ServiceProviderReview
        fields = (
            "id",
            "rating",
            "review_text",
            "reviewed_by",
            "maintenance_details",
            "created_on",
        )


class ServiceProviderDetailSerializer(BaseSerializer):
    profile_image_id = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="profile_image",
        required=False,
    )
    profile_image = AssetSerializer(read_only=True)
    documents = ServiceProviderDocumentSerializer(read_only=True, many=True)
    recent_reviews = serializers.SerializerMethodField()
    rating_breakdown = serializers.SerializerMethodField()
    service_history_summary = serializers.SerializerMethodField()
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    work_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    home_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )
    fax = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone_number],
    )

    def get_recent_reviews(self, obj):
        reviews = obj.reviews.all().order_by("-created_on")[:5]
        return ServiceProviderReviewDetailSerializer(reviews, many=True).data

    def get_rating_breakdown(self, obj):
        reviews = obj.reviews.all()
        total_reviews = reviews.count()

        if total_reviews == 0:
            return {
                "5_star": 0,
                "4_star": 0,
                "3_star": 0,
                "2_star": 0,
                "1_star": 0,
            }

        breakdown = {}
        for star in [5, 4, 3, 2, 1]:
            count = reviews.filter(
                rating__gte=star - 0.5, rating__lt=star + 0.5
            ).count()
            percentage = round((count / total_reviews) * 100, 1)
            breakdown[f"{star}_star"] = percentage

        return breakdown

    def get_service_history_summary(self, obj):
        maintenance_records = Maintenance.objects.filter(assignee=obj)
        total = maintenance_records.count()
        completed = maintenance_records.filter(status="COMPLETED").count()
        in_progress = maintenance_records.filter(status="IN_PROGRESS").count()

        return {"total": total, "completed": completed, "in_progress": in_progress}

    class Meta:
        model = ServiceProvider
        fields = (
            # Basic Information
            "id",
            "display_id",
            "name",
            "contact_name",
            "profile_image_id",
            "profile_image",
            "service_type",
            "languages_known",
            # Description and License Information
            "description",
            "license_number",
            "registration_info",
            # Contact Information (from PhoneEmail mixin)
            "phone",
            "email",
            "work_phone",
            "home_phone",
            "fax",
            # Rating and Statistics
            "overall_rating",
            "average_rating",
            "review_count",
            "total_jobs",
            # Status
            "active",
            # Nested data
            "documents",
            "recent_reviews",
            "rating_breakdown",
            "service_history_summary",
            # Audit fields
            "created_on",
            "updated_on",
        )


class MaintenanceSerializer(BaseSerializer):
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(),
        write_only=True,
        source="unit",
        required=True,
    )
    unit = UnitDetailSerializer(read_only=True)
    resident_id = serializers.PrimaryKeyRelatedField(
        queryset=Resident.objects.all(),
        write_only=True,
        source="resident",
        required=False,
        allow_null=True,
    )
    resident = ResidentSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        write_only=True,
        source="assignee",
        required=False,
    )
    assignee = ServiceProviderSerializer(read_only=True)
    preferred_vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        write_only=True,
        source="preferred_vendor",
        required=False,
    )
    preferred_vendor = ServiceProviderSerializer(read_only=True)
    media_ids = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        write_only=True,
        source="media",
        required=False,
        many=True,
    )
    media = AssetSerializer(read_only=True, many=True)

    class Meta:
        model = Maintenance
        fields = "__all__"

    def validate(self, attrs):
        status = attrs.get("status")
        if status:
            if status == MaintenanceStatus.COMPLETED.value:
                if not self.instance or (
                    self.instance and not self.instance.resolved_date
                ):
                    attrs["resolved_date"] = datetime.now().date()
            if status == MaintenanceStatus.REJECTED.value:
                if not attrs.get("reject_reason"):
                    raise serializers.ValidationError(
                        code="missing_required_param",
                        detail=ERROR_DETAILS["missing_required_param"].format(
                            param="reject_reason"
                        ),
                    )
                if not self.instance or (
                    self.instance and not self.instance.reject_date
                ):
                    attrs["reject_date"] = datetime.now().date()
        return super().validate(attrs)


class MaintenanceStatusUpdateSerializer(BaseSerializer):
    class Meta:
        model = Maintenance
        fields = [
            "status",
            "reject_reason",
            "reject_notes",
        ]

    def validate(self, attrs):
        status = attrs.get("status")
        if not status:
            raise serializers.ValidationError(
                code="missing_required_param",
                detail=ERROR_DETAILS["missing_required_param"].format(param="status"),
            )

        if status == MaintenanceStatus.REJECTED.value:
            if not attrs.get("reject_reason"):
                raise serializers.ValidationError(
                    code="missing_required_param",
                    detail=ERROR_DETAILS["missing_required_param"].format(
                        param="reject_reason"
                    ),
                )

        return super().validate(attrs)


class MaintenanceAssignSerializer(BaseSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceProvider.objects.all(),
        source="assignee",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Maintenance
        fields = ["assignee_id"]
