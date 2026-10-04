from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import NavigationItem, NavPermission
from django.contrib.auth.models import AnonymousUser
from .permissions import IsAuthenticatedUser, HasNavigationPermission, HasAdminOnlyPermissions
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

class GetNavPermissionsView(APIView):

    permission_classes = [IsAuthenticatedUser]

    def get(self, request, *args, **kwargs):
        user = request.user

        if user is None or isinstance(user, AnonymousUser):
            return Response(
                {
                    "is_success": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        role_id = getattr(user, "role_id", None)
        subrole_id = getattr(user, "subrole_id", None)

        if role_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "User role not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        nav_filter = {
            "role_id": role_id,
        }

        if subrole_id is not None:
            nav_filter["subrole_id"] = subrole_id
        else:
            nav_filter["subrole_id__isnull"] = True

        nav_permissions = (
            NavPermission.objects
            .filter(**nav_filter)
            .select_related("navigation_item")
        )

        if not nav_permissions.exists():
            return Response(
                {
                    "is_success": False,
                    "message": "No navigation permissions found.",
                    "data": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission_map = {
            permission.navigation_item_id: permission
            for permission in nav_permissions
        }

        root_items = (
            NavigationItem.objects
            .filter(
                parent__isnull=True,
                is_active=True,
                id__in=permission_map.keys(),
            )
            .order_by("sort_order", "id")
        )

        response_data = []

        for nav_item in root_items:
            navigation_data = self._build_navigation_tree(
                nav_item,
                permission_map,
            )

            if navigation_data:
                response_data.append(navigation_data)

        return Response(
            {
                "is_success": True,
                "message": "Navigation permissions fetched successfully.",
                "data": response_data,
            },
            status=status.HTTP_200_OK,
        )

    def _build_navigation_tree(self, nav_item, permission_map):

        nav_permission = permission_map.get(nav_item.id)

        if not nav_permission or not nav_permission.can_view:
            return None

        navigation_data = {
            "role_id": nav_permission.role_id,
            "subrole_id": nav_permission.subrole_id,
            "nav_item_id": nav_item.id,
            "nav_item_name": nav_item.name,
            "nav_item_code": nav_item.code,
            "item_type": nav_item.item_type,
            "url": nav_item.url,
            "icon": nav_item.icon,
            "sort_order": nav_item.sort_order,
            "permissions": {
                "can_view": nav_permission.can_view,
                "can_create": nav_permission.can_create,
                "can_update": nav_permission.can_update,
                "can_delete": nav_permission.can_delete,
            },
            "children": [],
        }

        children = (
            NavigationItem.objects
            .filter(
                parent=nav_item,
                is_active=True,
            )
            .order_by("sort_order", "id")
        )

        for child in children:
            child_data = self._build_navigation_tree(
                child,
                permission_map,
            )

            if child_data:
                navigation_data["children"].append(child_data)

        return navigation_data


class CreatePermissionsView(APIView):

    permission_classes = [IsAuthenticatedUser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        data = request.data
        user = request.user

        # Authentication validation
        if user is None or isinstance(user, AnonymousUser):
            return Response(
                {
                    "is_success": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Validate authenticated user's role
        user_role_id = getattr(user, "role_id", None)

        if user_role_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "User role not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Required fields
        role_id = data.get("role_id")
        subrole_id = data.get("subrole_id")
        navigation_item_id = data.get("navigation_item_id")

        if role_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "role_id is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if navigation_item_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "navigation_item_id is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate role_id
        try:
            role_id = int(role_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "role_id must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate navigation_item_id
        try:
            navigation_item_id = int(navigation_item_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "navigation_item_id must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate subrole_id
        if subrole_id in ("", None):
            subrole_id = None
        else:
            try:
                subrole_id = int(subrole_id)
            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": "subrole_id must be a valid integer.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Get navigation item
        try:
            navigation_item = NavigationItem.objects.get(
                id=navigation_item_id,
                is_active=True,
            )
        except NavigationItem.DoesNotExist:
            return Response(
                {
                    "is_success": False,
                    "message": "Navigation item not found.",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Permission values
        can_view = data.get("can_view", False)
        can_create = data.get("can_create", False)
        can_update = data.get("can_update", False)
        can_delete = data.get("can_delete", False)

        permissions = {
            "can_view": can_view,
            "can_create": can_create,
            "can_update": can_update,
            "can_delete": can_delete,
        }

        # Validate boolean values
        for field, value in permissions.items():
            if not isinstance(value, bool):
                return Response(
                    {
                        "is_success": False,
                        "message": f"{field} must be a boolean.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Check duplicate permission
        permission_filter = {
            "role_id": role_id,
            "navigation_item": navigation_item,
        }

        if subrole_id is None:
            permission_filter["subrole_id__isnull"] = True
        else:
            permission_filter["subrole_id"] = subrole_id

        if NavPermission.objects.filter(**permission_filter).exists():
            return Response(
                {
                    "is_success": False,
                    "message": (
                        "Permission already exists for this role, "
                        "subrole and navigation item."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Create permission
        nav_permission = NavPermission.objects.create(
            role_id=role_id,
            subrole_id=subrole_id,
            navigation_item=navigation_item,
            can_view=can_view,
            can_create=can_create,
            can_update=can_update,
            can_delete=can_delete,
        )

        # Response
        response_data = {
            "id": nav_permission.id,
            "role_id": nav_permission.role_id,
            "subrole_id": nav_permission.subrole_id,
            "navigation_item_id": nav_permission.navigation_item_id,
            "navigation_item_name": navigation_item.name,
            "navigation_item_code": navigation_item.code,
            "permissions": {
                "can_view": nav_permission.can_view,
                "can_create": nav_permission.can_create,
                "can_update": nav_permission.can_update,
                "can_delete": nav_permission.can_delete,
            },
        }

        return Response(
            {
                "is_success": True,
                "message": "Navigation permission created successfully.",
                "data": response_data,
            },
            status=status.HTTP_201_CREATED,
        )




class UpdateRolePermissionsView(APIView):

    permission_classes = [IsAuthenticatedUser]

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        user = request.user

        # ---------------------------------------------------------
        # Authentication
        # ---------------------------------------------------------
        if user is None or isinstance(user, AnonymousUser):
            return Response(
                {
                    "is_success": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = request.data

        # ---------------------------------------------------------
        # Get payload
        # ---------------------------------------------------------
        role_id = data.get("role_id")
        subrole_id = data.get("subrole_id")
        permissions = data.get("permissions")

        # ---------------------------------------------------------
        # Validate role_id
        # ---------------------------------------------------------
        if role_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "role_id is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            role_id = int(role_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "role_id must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role_id <= 0:
            return Response(
                {
                    "is_success": False,
                    "message": "role_id must be greater than 0.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate subrole_id
        # ---------------------------------------------------------
        if subrole_id in ("", None):
            subrole_id = None
        else:
            try:
                subrole_id = int(subrole_id)
            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": "subrole_id must be a valid integer.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if subrole_id <= 0:
                return Response(
                    {
                        "is_success": False,
                        "message": "subrole_id must be greater than 0.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---------------------------------------------------------
        # Validate permissions
        # ---------------------------------------------------------
        if permissions is None:
            return Response(
                {
                    "is_success": False,
                    "message": "permissions is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(permissions, list):
            return Response(
                {
                    "is_success": False,
                    "message": "permissions must be a list.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        permission_fields = [
            "can_view",
            "can_create",
            "can_update",
            "can_delete",
        ]

        navigation_item_ids = []

        # ---------------------------------------------------------
        # Validate each permission
        # ---------------------------------------------------------
        for index, permission in enumerate(permissions):

            if not isinstance(permission, dict):
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"permissions[{index}] must be an object."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            navigation_item_id = permission.get("navigation_item_id")

            if navigation_item_id is None:
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"permissions[{index}].navigation_item_id "
                            "is required."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                navigation_item_id = int(navigation_item_id)
            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"permissions[{index}].navigation_item_id "
                            "must be a valid integer."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if navigation_item_id <= 0:
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"permissions[{index}].navigation_item_id "
                            "must be greater than 0."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Prevent duplicate navigation items
            if navigation_item_id in navigation_item_ids:
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"Duplicate navigation_item_id "
                            f"{navigation_item_id} found."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            navigation_item_ids.append(navigation_item_id)

            # Validate permission flags
            for field in permission_fields:

                value = permission.get(field, False)

                if not isinstance(value, bool):
                    return Response(
                        {
                            "is_success": False,
                            "message": (
                                f"permissions[{index}].{field} "
                                "must be a boolean."
                            ),
                            "data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        # ---------------------------------------------------------
        # Get navigation items
        # ---------------------------------------------------------
        navigation_items = NavigationItem.objects.filter(
            id__in=navigation_item_ids,
            is_active=True,
        )

        navigation_item_map = {
            item.id: item
            for item in navigation_items
        }

        # ---------------------------------------------------------
        # Check missing navigation items
        # ---------------------------------------------------------
        missing_items = [
            item_id
            for item_id in navigation_item_ids
            if item_id not in navigation_item_map
        ]

        if missing_items:
            return Response(
                {
                    "is_success": False,
                    "message": "One or more navigation items were not found.",
                    "data": {
                        "missing_navigation_item_ids": missing_items
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---------------------------------------------------------
        # Delete existing permissions
        # ---------------------------------------------------------
        delete_filter = {
            "role_id": role_id,
        }

        if subrole_id is None:
            delete_filter["subrole_id__isnull"] = True
        else:
            delete_filter["subrole_id"] = subrole_id

        deleted_count, _ = NavPermission.objects.filter(
            **delete_filter
        ).delete()

        # ---------------------------------------------------------
        # Create fresh permissions
        # ---------------------------------------------------------
        new_permissions = []

        for permission in permissions:

            navigation_item_id = int(
                permission["navigation_item_id"]
            )

            new_permissions.append(
                NavPermission(
                    role_id=role_id,
                    subrole_id=subrole_id,
                    navigation_item_id=navigation_item_id,
                    can_view=permission.get("can_view", False),
                    can_create=permission.get("can_create", False),
                    can_update=permission.get("can_update", False),
                    can_delete=permission.get("can_delete", False),
                )
            )

        created_permissions = NavPermission.objects.bulk_create(
            new_permissions
        )

        # ---------------------------------------------------------
        # Response
        # ---------------------------------------------------------
        response_permissions = []

        for nav_permission in created_permissions:

            navigation_item = navigation_item_map[
                nav_permission.navigation_item_id
            ]

            response_permissions.append(
                {
                    "id": nav_permission.id,
                    "navigation_item_id": nav_permission.navigation_item_id,
                    "navigation_item_name": navigation_item.name,
                    "navigation_item_code": navigation_item.code,
                    "item_type": navigation_item.item_type,
                    "permissions": {
                        "can_view": nav_permission.can_view,
                        "can_create": nav_permission.can_create,
                        "can_update": nav_permission.can_update,
                        "can_delete": nav_permission.can_delete,
                    },
                }
            )

        return Response(
            {
                "is_success": True,
                "message": "Role navigation permissions updated successfully.",
                "data": {
                    "role_id": role_id,
                    "subrole_id": subrole_id,
                    "deleted_permissions": deleted_count,
                    "created_permissions": len(created_permissions),
                    "permissions": response_permissions,
                },
            },
            status=status.HTTP_200_OK,
        )

class GetRoleNavItemsView(APIView):
    permission_classes = [IsAuthenticatedUser, HasAdminOnlyPermissions]

    def get(self, request, *args, **kwargs):
        user = request.user

        # ---------------------------------------------------------
        # Authentication
        # ---------------------------------------------------------
        if user is None or isinstance(user, AnonymousUser):
            return Response(
                {
                    "is_success": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ---------------------------------------------------------
        # Query Parameters
        # ---------------------------------------------------------
        role_id = request.GET.get("role_id")
        subrole_id = request.GET.get("subrole_id")
        limit = request.GET.get("limit", 10)
        offset = request.GET.get("offset", 0)

        # ---------------------------------------------------------
        # Validate role_id
        # ---------------------------------------------------------
        if role_id is None:
            return Response(
                {
                    "is_success": False,
                    "message": "role_id is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            role_id = int(role_id)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "role_id must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if role_id <= 0:
            return Response(
                {
                    "is_success": False,
                    "message": "role_id must be greater than 0.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate subrole_id
        # ---------------------------------------------------------
        if subrole_id in ("", None):
            subrole_id = None
        else:
            try:
                subrole_id = int(subrole_id)
            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": "subrole_id must be a valid integer.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if subrole_id <= 0:
                return Response(
                    {
                        "is_success": False,
                        "message": "subrole_id must be greater than 0.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---------------------------------------------------------
        # Validate limit
        # ---------------------------------------------------------
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "limit must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if limit <= 0:
            return Response(
                {
                    "is_success": False,
                    "message": "limit must be greater than 0.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate offset
        # ---------------------------------------------------------
        try:
            offset = int(offset)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "offset must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if offset < 0:
            return Response(
                {
                    "is_success": False,
                    "message": "offset must be greater than or equal to 0.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Get permissions for role/subrole
        # ---------------------------------------------------------
        permission_filter = {
            "role_id": role_id,
        }

        if subrole_id is None:
            permission_filter["subrole_id__isnull"] = True
        else:
            permission_filter["subrole_id"] = subrole_id

        nav_permissions = (
            NavPermission.objects
            .filter(**permission_filter)
            .select_related("navigation_item")
        )

        permission_map = {
            permission.navigation_item_id: permission
            for permission in nav_permissions
        }

        # ---------------------------------------------------------
        # Get all active top-level menus
        # ---------------------------------------------------------
        menus_queryset = (
            NavigationItem.objects
            .filter(
                item_type=NavigationItem.ItemType.MENU,
                parent__isnull=True,
                is_active=True,
            )
            .prefetch_related(
                "children__children__children"
            )
            .order_by(
                "sort_order",
                "id",
            )
        )

        # ---------------------------------------------------------
        # Total count before pagination
        # ---------------------------------------------------------
        total_count = menus_queryset.count()

        # ---------------------------------------------------------
        # Apply limit & offset
        # ---------------------------------------------------------
        menus = menus_queryset[offset:offset + limit]

        # ---------------------------------------------------------
        # Build navigation tree
        # ---------------------------------------------------------
        response_data = []

        for menu in menus:
            menu_data = self._build_navigation_tree(
                menu,
                permission_map,
            )

            response_data.append(menu_data)

        # ---------------------------------------------------------
        # Response
        # ---------------------------------------------------------
        return Response(
            {
                "is_success": True,
                "message": "Role navigation list fetched successfully.",
                "data": {
                    "role_id": role_id,
                    "subrole_id": subrole_id,
                    "limit": limit,
                    "offset": offset,
                    "menus": response_data,
                },
                "total_count": total_count,
            },
            status=status.HTTP_200_OK,
        )

    # =============================================================
    # Build Navigation Tree
    # =============================================================

    def _build_navigation_tree(
        self,
        nav_item,
        permission_map,
    ):
        nav_permission = permission_map.get(
            nav_item.id
        )

        # ---------------------------------------------------------
        # Permission status
        # ---------------------------------------------------------
        permission_active = bool(
            nav_permission and nav_permission.can_view
        )

        # ---------------------------------------------------------
        # Permission values
        # ---------------------------------------------------------
        if nav_permission:
            permissions = {
                "can_view": nav_permission.can_view,
                "can_create": nav_permission.can_create,
                "can_update": nav_permission.can_update,
                "can_delete": nav_permission.can_delete,
            }
        else:
            permissions = {
                "can_view": False,
                "can_create": False,
                "can_update": False,
                "can_delete": False,
            }

        # ---------------------------------------------------------
        # Navigation data
        # ---------------------------------------------------------
        navigation_data = {
            "navigation_item_id": nav_item.id,
            "name": nav_item.name,
            "code": nav_item.code,
            "item_type": nav_item.item_type,
            "url": nav_item.url,
            "icon": nav_item.icon,
            "sort_order": nav_item.sort_order,
            "is_active": nav_item.is_active,
            "permission_active": permission_active,
            "permissions": permissions,
            "children": [],
        }

        # ---------------------------------------------------------
        # Children
        # ---------------------------------------------------------
        children = nav_item.children.all().order_by(
            "sort_order",
            "id",
        )

        for child in children:
            child_data = self._build_navigation_tree(
                child,
                permission_map,
            )

            navigation_data["children"].append(
                child_data
            )

        return navigation_data


class CreateNavItemsView(APIView):

    permission_classes = [
        IsAuthenticatedUser,
        HasAdminOnlyPermissions,
    ]

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        user = request.user

        # ---------------------------------------------------------
        # Authentication
        # ---------------------------------------------------------

        if user is None or isinstance(user, AnonymousUser):
            return Response(
                {
                    "is_success": False,
                    "message": "Authentication credentials were not provided.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = request.data

        # ---------------------------------------------------------
        # Required fields
        # ---------------------------------------------------------

        name = data.get("name")
        code = data.get("code")
        item_type = data.get("item_type")
        parent_id = data.get("parent_id")

        url = data.get("url")
        icon = data.get("icon")
        sort_order = data.get("sort_order", 0)
        is_active = data.get("is_active", True)
        metadata = data.get("metadata", {})

        # ---------------------------------------------------------
        # Name
        # ---------------------------------------------------------

        if not name:
            return Response(
                {
                    "is_success": False,
                    "message": "name is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        name = str(name).strip()

        if not name:
            return Response(
                {
                    "is_success": False,
                    "message": "name cannot be empty.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Code
        # ---------------------------------------------------------

        if not code:
            return Response(
                {
                    "is_success": False,
                    "message": "code is required.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = str(code).strip().lower()

        if not code:
            return Response(
                {
                    "is_success": False,
                    "message": "code cannot be empty.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Item type
        # ---------------------------------------------------------

        valid_item_types = {
            NavigationItem.ItemType.MENU,
            NavigationItem.ItemType.SUBMENU,
            NavigationItem.ItemType.PAGE,
            NavigationItem.ItemType.WIDGET,
        }

        if item_type not in valid_item_types:
            return Response(
                {
                    "is_success": False,
                    "message": (
                        "item_type must be one of: "
                        "menu, submenu, page, widget."
                    ),
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate parent
        # ---------------------------------------------------------

        parent = None

        if item_type == NavigationItem.ItemType.MENU:

            if parent_id not in (None, "", 0, "0"):
                return Response(
                    {
                        "is_success": False,
                        "message": "Menu cannot have a parent.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:

            if parent_id in (None, "", 0, "0"):
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"parent_id is required for {item_type}."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                parent_id = int(parent_id)
            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": "parent_id must be a valid integer.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                parent = NavigationItem.objects.get(
                    id=parent_id
                )
            except NavigationItem.DoesNotExist:
                return Response(
                    {
                        "is_success": False,
                        "message": "Parent navigation item not found.",
                        "data": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # -----------------------------------------------------
            # Validate hierarchy
            # -----------------------------------------------------

            allowed_parent_types = {
                NavigationItem.ItemType.SUBMENU:
                    NavigationItem.ItemType.MENU,

                NavigationItem.ItemType.PAGE:
                    NavigationItem.ItemType.SUBMENU,

                NavigationItem.ItemType.WIDGET:
                    NavigationItem.ItemType.PAGE,
            }

            expected_parent_type = allowed_parent_types[item_type]

            if parent.item_type != expected_parent_type:
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            f"{item_type} can only be created "
                            f"under {expected_parent_type}."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ---------------------------------------------------------
        # Validate sort_order
        # ---------------------------------------------------------

        try:
            sort_order = int(sort_order)
        except (TypeError, ValueError):
            return Response(
                {
                    "is_success": False,
                    "message": "sort_order must be a valid integer.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sort_order < 0:
            return Response(
                {
                    "is_success": False,
                    "message": "sort_order cannot be negative.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate is_active
        # ---------------------------------------------------------

        if not isinstance(is_active, bool):
            return Response(
                {
                    "is_success": False,
                    "message": "is_active must be a boolean.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Validate metadata
        # ---------------------------------------------------------

        if not isinstance(metadata, dict):
            return Response(
                {
                    "is_success": False,
                    "message": "metadata must be an object.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Check duplicate code
        # ---------------------------------------------------------

        if NavigationItem.objects.filter(code=code).exists():
            return Response(
                {
                    "is_success": False,
                    "message": (
                        "Navigation item with this code already exists."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ---------------------------------------------------------
        # Create NavigationItem
        # ---------------------------------------------------------

        navigation_item = NavigationItem(
            name=name,
            code=code,
            item_type=item_type,
            parent=parent,
            url=url,
            icon=icon,
            sort_order=sort_order,
            is_active=is_active,
            metadata=metadata,
        )

        # ---------------------------------------------------------
        # Model validation
        # ---------------------------------------------------------

        try:
            navigation_item.full_clean()
        except ValidationError as exc:
            return Response(
                {
                    "is_success": False,
                    "message": "Invalid navigation item.",
                    "data": exc.message_dict,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---------------------------------------------------------
        # Save
        # ---------------------------------------------------------

        try:
            navigation_item.save()

        except IntegrityError:
            return Response(
                {
                    "is_success": False,
                    "message": (
                        "Navigation item could not be created. "
                        "The code may already exist."
                    ),
                    "data": None,
                },
                status=status.HTTP_409_CONFLICT,
            )

        # ---------------------------------------------------------
        # Response
        # ---------------------------------------------------------

        response_data = {
            "id": navigation_item.id,
            "name": navigation_item.name,
            "code": navigation_item.code,
            "item_type": navigation_item.item_type,
            "parent_id": navigation_item.parent_id,
            "parent_name": (
                navigation_item.parent.name
                if navigation_item.parent
                else None
            ),
            "url": navigation_item.url,
            "icon": navigation_item.icon,
            "sort_order": navigation_item.sort_order,
            "is_active": navigation_item.is_active,
            "metadata": navigation_item.metadata,
            "created_at": navigation_item.created_at,
            "updated_at": navigation_item.updated_at,
        }

        return Response(
            {
                "is_success": True,
                "message": "Navigation item created successfully.",
                "data": response_data,
            },
            status=status.HTTP_201_CREATED,
        )


class UpdateNavItemsView(APIView):
    permission_classes = [
        IsAuthenticatedUser,
        HasAdminOnlyPermissions,
    ]

    @transaction.atomic
    def post(self, request):
        try:
            user = getattr(request, "user", None)

            if user is None or user.__class__.__name__ == "AnonymousUser":
                return Response(
                    {
                        "is_success": False,
                        "message": "Authentication credentials were not provided.",
                        "data": None,
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            nav_item_id = request.data.get("nav_item_id")

            if not nav_item_id:
                return Response(
                    {
                        "is_success": False,
                        "message": "nav_item_id is required.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                nav_item = (
                    NavigationItem.objects
                    .select_related("parent")
                    .get(id=nav_item_id)
                )
            except NavigationItem.DoesNotExist:
                return Response(
                    {
                        "is_success": False,
                        "message": "Navigation item not found.",
                        "data": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            name = request.data.get("name")
            code = request.data.get("code")
            item_type = request.data.get("item_type")
            parent_id = request.data.get("parent_id")

            url = request.data.get("url")
            icon = request.data.get("icon")

            sort_order = request.data.get(
                "sort_order",
                nav_item.sort_order,
            )

            is_active = request.data.get(
                "is_active",
                nav_item.is_active,
            )

            metadata = request.data.get(
                "metadata",
                nav_item.metadata,
            )

            # -------------------------
            # Required fields
            # -------------------------

            if not name:
                return Response(
                    {
                        "is_success": False,
                        "message": "name is required.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not code:
                return Response(
                    {
                        "is_success": False,
                        "message": "code is required.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not item_type:
                return Response(
                    {
                        "is_success": False,
                        "message": "item_type is required.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # Normalize values
            # -------------------------

            name = str(name).strip()
            code = str(code).strip().lower()
            item_type = str(item_type).strip().lower()

            valid_item_types = {
                NavigationItem.ItemType.MENU,
                NavigationItem.ItemType.SUBMENU,
                NavigationItem.ItemType.PAGE,
                NavigationItem.ItemType.WIDGET,
            }

            if item_type not in valid_item_types:
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            "Invalid item_type. "
                            "Allowed values: menu, submenu, page, widget."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # Prevent item type change
            # if children exist
            # -------------------------

            if (
                item_type != nav_item.item_type
                and nav_item.children.exists()
            ):
                return Response(
                    {
                        "is_success": False,
                        "message": (
                            "Cannot change item_type because this "
                            "navigation item has children."
                        ),
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # Parent validation
            # -------------------------

            if item_type == NavigationItem.ItemType.MENU:

                if parent_id not in (None, "", 0, "0"):
                    return Response(
                        {
                            "is_success": False,
                            "message": "Menu cannot have a parent.",
                            "data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                parent = None

            else:

                if parent_id in (None, "", 0, "0"):
                    return Response(
                        {
                            "is_success": False,
                            "message": (
                                f"{item_type} must have a parent."
                            ),
                            "data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    parent = NavigationItem.objects.get(
                        id=parent_id
                    )
                except NavigationItem.DoesNotExist:
                    return Response(
                        {
                            "is_success": False,
                            "message": "Parent navigation item not found.",
                            "data": None,
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Prevent circular hierarchy
                if parent.id == nav_item.id:
                    return Response(
                        {
                            "is_success": False,
                            "message": (
                                "Navigation item cannot be its own parent."
                            ),
                            "data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                ancestor = parent

                while ancestor:
                    if ancestor.id == nav_item.id:
                        return Response(
                            {
                                "is_success": False,
                                "message": (
                                    "Circular navigation hierarchy "
                                    "is not allowed."
                                ),
                                "data": None,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    ancestor = ancestor.parent

                allowed_parents = {
                    NavigationItem.ItemType.SUBMENU: {
                        NavigationItem.ItemType.MENU
                    },
                    NavigationItem.ItemType.PAGE: {
                        NavigationItem.ItemType.SUBMENU
                    },
                    NavigationItem.ItemType.WIDGET: {
                        NavigationItem.ItemType.PAGE
                    },
                }

                allowed = allowed_parents[item_type]

                if parent.item_type not in allowed:
                    return Response(
                        {
                            "is_success": False,
                            "message": (
                                f"{item_type} can only have "
                                f"{', '.join(allowed)} as parent."
                            ),
                            "data": None,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # -------------------------
            # sort_order validation
            # -------------------------

            try:
                sort_order = int(sort_order)

                if sort_order < 0:
                    raise ValueError

            except (TypeError, ValueError):
                return Response(
                    {
                        "is_success": False,
                        "message": "sort_order must be a non-negative integer.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # is_active validation
            # -------------------------

            if not isinstance(is_active, bool):
                return Response(
                    {
                        "is_success": False,
                        "message": "is_active must be a boolean.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # metadata validation
            # -------------------------

            if not isinstance(metadata, dict):
                return Response(
                    {
                        "is_success": False,
                        "message": "metadata must be an object.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -------------------------
            # Duplicate code
            # -------------------------

            if NavigationItem.objects.filter(
                code=code
            ).exclude(
                id=nav_item.id
            ).exists():

                return Response(
                    {
                        "is_success": False,
                        "message": "Navigation item code already exists.",
                        "data": None,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # -------------------------
            # Update
            # -------------------------

            nav_item.name = name
            nav_item.code = code
            nav_item.item_type = item_type
            nav_item.parent = parent
            nav_item.url = url
            nav_item.icon = icon
            nav_item.sort_order = sort_order
            nav_item.is_active = is_active
            nav_item.metadata = metadata

            nav_item.full_clean()
            nav_item.save()

            return Response(
                {
                    "is_success": True,
                    "message": "Navigation item updated successfully.",
                    "data": {
                        "id": nav_item.id,
                        "name": nav_item.name,
                        "code": nav_item.code,
                        "item_type": nav_item.item_type,
                        "parent_id": nav_item.parent_id,
                        "url": nav_item.url,
                        "icon": nav_item.icon,
                        "sort_order": nav_item.sort_order,
                        "is_active": nav_item.is_active,
                        "metadata": nav_item.metadata,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ValidationError as exc:
            return Response(
                {
                    "is_success": False,
                    "message": "Validation error.",
                    "data": exc.message_dict,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "is_success": False,
                    "message": "Failed to update navigation item.",
                    "data": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )