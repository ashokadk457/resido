from common.serializers import BaseSerializer, serializers
from data.models import ReasonCategory, Reason


class ReasonCategorySerializer(BaseSerializer):
    class Meta:
        model = ReasonCategory
        fields = "__all__"


class ReasonSerializer(BaseSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ReasonCategory.objects.all(),
        write_only=True,
        source="category",
        required=False,
    )
    category = ReasonCategorySerializer(read_only=True)

    class Meta:
        model = Reason
        fields = "__all__"


class ReasonBulkUploadSerializer(BaseSerializer):
    class Meta:
        model = Reason
        fields = "__all__"
