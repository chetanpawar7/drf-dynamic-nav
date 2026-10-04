from django.urls import path
from .views import GetNavPermissionsView, CreatePermissionsView, UpdateRolePermissionsView, GetRoleNavItemsView, CreateNavItemsView, UpdateNavItemsView
app_name = "drf_dynamic_nav"

urlpatterns = [
    # permissions apis
    path("get-nav-permissions/", GetNavPermissionsView.as_view(), name="get_nav_permissions"),
    path("permissions/create/", CreatePermissionsView.as_view(), name="create_permissions"),
    path("permissions/update/", UpdateRolePermissionsView.as_view(), name="update_role_permissions"),

    # navitems apis
    path("get-role-nav-items/", GetRoleNavItemsView.as_view(), name="get-role-nav-items"),
    path("nav-items/create/", CreateNavItemsView.as_view(), name="create_nav_items"),
    path("nav-items/update/", UpdateNavItemsView.as_view(), name="update_nav_items"),

]