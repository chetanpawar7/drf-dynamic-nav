from rest_framework.permissions import BasePermission
from django.conf import settings

class IsAuthenticatedUser(BasePermission):
    message = "Authentication credentials were not provided."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is None:
            return False

        # DRF sets AnonymousUser when authentication did not succeed.
        if user.__class__.__name__ == "AnonymousUser":
            return False

        # Custom UserMaster returned by your JWT authentication.
        return True


class HasNavigationPermission(BasePermission):
    """
    Checks CRUD permission for a navigation item.

    Set the required permission on the view:

        required_permission = "can_view"
        required_permission = "can_create"
        required_permission = "can_update"
        required_permission = "can_delete"
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)

        if user is None:
            return False

        role_id = getattr(user, "role_id", None)

        if role_id is None:
            return False

        return True



class HasAdminOnlyPermissions(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is None:
            return False
        
        role_id = getattr(user, "role_id", None)

        if role_id is None:
            return False

        
        dynamic_nav = getattr(settings, "DYNAMIC_NAV", {})

        admin_role_ids = dynamic_nav.get("ADMIN_ROLE_IDS", [])

        return role_id in admin_role_ids