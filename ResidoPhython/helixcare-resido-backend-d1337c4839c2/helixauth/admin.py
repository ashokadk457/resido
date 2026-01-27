from django.contrib import admin

from .models import (
    SecurityQuestion,
    UserSecurityQuestion,
    VerificationCode,
    HelixUser,
    UserRole,
    Module,
    ModuleComposition,
    ModulePermission,
    Entity,
    EntityAttributeComposition,
)


class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = (
        "user_id",
        "code",
        "channel",
        "user_type",
        "created_on",
        "updated_on",
    )
    ordering = ("-created_on",)

    # def email(self, obj):
    #     return obj.user.email


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role_name",
        "description",
        "is_role_active",
        "seeded",
        "created_on",
        "updated_on",
    )


@admin.register(HelixUser)
class HelixUserAdmin(admin.ModelAdmin):
    search_fields = ("email",)
    list_display = ("name", "email", "status", "locked")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name")


@admin.register(ModuleComposition)
class ModuleCompAdmin(admin.ModelAdmin):
    list_display = ("module", "entity")


@admin.register(ModulePermission)
class ModulePermAdmin(admin.ModelAdmin):
    list_display = ("module", "role")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("entity", "app_name")


@admin.register(EntityAttributeComposition)
class EntityAttributeCompositionAdmin(admin.ModelAdmin):
    list_display = ("entity", "attribute")
    search_fields = (
        "entity__entity",
        "attribute",
    )


admin.site.register(VerificationCode, VerificationCodeAdmin)
admin.site.register(SecurityQuestion)
admin.site.register(UserSecurityQuestion)
