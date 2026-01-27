from django.contrib import admin
from .models import (
    Location,
    Property,
    Customer,
)

# Register your models here.

admin.site.register(Location)
admin.site.register(Property)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_on",
        "updated_on",
    )
    search_fields = ["id", "name", "name"]
    ordering = ("-created_on",)
