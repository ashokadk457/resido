from django.contrib import admin

from .models import CPTData, Lookup, UIMetaData, CPTCategoryValue


@admin.register(Lookup)
class LookupAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "value",
        "display_name",
        "display_order",
        "active",
        "favorite",
    )
    list_filter = ("name",)


admin.site.register(CPTData)
admin.site.register(CPTCategoryValue)
admin.site.register(UIMetaData)
