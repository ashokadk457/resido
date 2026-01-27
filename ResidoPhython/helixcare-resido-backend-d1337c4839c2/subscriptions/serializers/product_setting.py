from hb_core.serializers import StandardModelSerializer

from subscriptions.models.product_setting import ProductSetting


class ProductSettingSerializer(StandardModelSerializer):
    class Meta:
        model = ProductSetting
        fields = "__all__"
