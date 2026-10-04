from django.contrib import admin

from .models import NavigationItem, NavPermission


@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "code",
        "item_type",
        "parent",
        "sort_order",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "item_type",
        "is_active",
    )

    search_fields = (
        "name",
        "code",
    )

    ordering = (
        "sort_order",
        "id",
    )

    list_select_related = (
        "parent",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "code",
                    "item_type",
                    "parent",
                )
            },
        ),
        (
            "Navigation",
            {
                "fields": (
                    "url",
                    "icon",
                    "sort_order",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "metadata",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(NavPermission)
class NavPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "role_id",
        "subrole_id",
        "navigation_item",
        "can_view",
        "can_create",
        "can_update",
        "can_delete",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "can_view",
        "can_create",
        "can_update",
        "can_delete",
    )

    search_fields = (
        "navigation_item__name",
        "navigation_item__code",
        "role_id",
        "subrole_id",
    )

    ordering = (
        "role_id",
        "subrole_id",
        "id",
    )

    list_select_related = (
        "navigation_item",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Role",
            {
                "fields": (
                    "role_id",
                    "subrole_id",
                )
            },
        ),
        (
            "Navigation",
            {
                "fields": (
                    "navigation_item",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "can_view",
                    "can_create",
                    "can_update",
                    "can_delete",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)