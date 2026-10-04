from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

DYNAMIC_NAV_CONFIG = getattr(settings, "DYNAMIC_NAV", {})
NAVIGATION_ITEM_TABLE = DYNAMIC_NAV_CONFIG.get(
    "NAVIGATION_ITEM_TABLE_NAME",
    "navigation_item",
)
NAV_PERMISSION_TABLE = DYNAMIC_NAV_CONFIG.get(
    "NAV_PERMISSION_TABLE_NAME",
    "nav_permission",
)


class NavigationItem(models.Model):
    class ItemType(models.TextChoices):
        MENU = "menu", "Menu"
        SUBMENU = "submenu", "SubMenu"
        PAGE = "page", "Page"
        WIDGET = "widget", "Widget"

    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=150)

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
    )

    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        db_index=True,
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    url = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    sort_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(
        default=True,
        db_index=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = NAVIGATION_ITEM_TABLE

        ordering = ["sort_order", "id"]

        indexes = [
            models.Index(
                fields=["item_type", "is_active"],
                name="idx_nav_item_type_active",
            ),
            models.Index(
                fields=["parent", "sort_order"],
                name="idx_nav_parent_order",
            ),
        ]

    def clean(self):
        """
        Validate navigation hierarchy.

        Allowed:

            Menu
              └── SubMenu
                    └── Page
                          └── Widget
        """

        if not self.parent:
            # Only Menu can exist at root level.
            if self.item_type != self.ItemType.MENU:
                raise ValidationError({
                    "item_type": "Only Menu items can exist at root level."
                })

            return

        if self.parent_id == self.id:
            raise ValidationError({
                "parent": "Navigation item cannot be its own parent."
            })

        allowed_parents = {
            self.ItemType.SUBMENU: {
                self.ItemType.MENU,
            },
            self.ItemType.PAGE: {
                self.ItemType.SUBMENU,
            },
            self.ItemType.WIDGET: {
                self.ItemType.PAGE,
            },
        }

        allowed = allowed_parents.get(self.item_type, set())

        if self.parent.item_type not in allowed:
            raise ValidationError({
                "parent": (
                    f"{self.item_type} cannot have "
                    f"{self.parent.item_type} as parent."
                )
            })

        # Prevent circular hierarchy.
        ancestor = self.parent

        while ancestor:
            if ancestor.pk == self.pk:
                raise ValidationError({
                    "parent": "Circular navigation hierarchy is not allowed."
                })

            ancestor = ancestor.parent

    def __str__(self):
        return f"{self.name} ({self.item_type})"


class NavPermission(models.Model):
    id = models.BigAutoField(primary_key=True)

    role_id = models.BigIntegerField(
        db_index=True,
        help_text="External Role ID",
    )

    subrole_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional external SubRole ID",
    )

    navigation_item = models.ForeignKey(
        "NavigationItem",
        on_delete=models.CASCADE,
        related_name="nav_permissions",
    )

    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = NAV_PERMISSION_TABLE

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "role_id",
                    "subrole_id",
                    "navigation_item",
                ],
                name="unique_role_subrole_navigation",
            )
        ]

        indexes = [
            models.Index(
                fields=["role_id", "subrole_id"],
                name="idx_role_subrole",
            ),
            models.Index(
                fields=["role_id", "navigation_item"],
                name="idx_role_navigation",
            ),
        ]

    def __str__(self):
        return (
            f"Role={self.role_id}, "
            f"SubRole={self.subrole_id}, "
            f"Item={self.navigation_item.name}"
        )