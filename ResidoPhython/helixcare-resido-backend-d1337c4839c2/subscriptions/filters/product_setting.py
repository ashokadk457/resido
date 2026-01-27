from hb_core.filters import StandardAPIFilter

from subscriptions.models.product_setting import ProductSetting


class ProductSettingFilter(StandardAPIFilter):
    class Meta:
        model = ProductSetting
        fields = [
            "id",
            "name",
            "visible_name",
            "category",
            "seeded",
            "active",
        ]
