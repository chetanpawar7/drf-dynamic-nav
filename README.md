# DRF Dynamic Navigation
PYPI PACKAGE LINK : https://pypi.org/project/drf-dynamic-nav/
A reusable Django REST Framework package for building **dynamic, role-based navigation systems**.

`drf-dynamic-nav` allows you to manage menus, submenus, pages, widgets, and permissions dynamically from the database instead of hardcoding navigation logic in your frontend.

It is designed for applications where different users or roles need access to different parts of the application.

---

## Features

- Dynamic navigation management

- Menu → SubMenu → Page → Widget hierarchy

- Role-based navigation permissions

- SubRole-based permissions

- External User and Role IDs supported

- No hard dependency on Django's built-in `auth_user`

- Custom authentication support

- Django REST Framework integration

- Database-driven navigation

- Active/inactive navigation items

- API-based navigation retrieval

- Easy integration with existing Django projects

- Customizable database table names

- Suitable for admin dashboards, enterprise applications, and SaaS applications

---

## Navigation Hierarchy

The package follows this structure:

```text
Menu
 └── SubMenu
      └── Page
           └── Widget
```

Example:

```text
Dashboard (Menu)
├── Reports  (Submenu)
│   ├── Sales Report (Page)
│   │   ├── Export Button  (Widget)
│   │   └── Filter Button
│   └── Inventory Report
│       └── Export Button
│
└── Settings
    ├── User Management
    └── Role Management
```

Permissions can be assigned at the required navigation level.

---

## Requirements

- Python 3.10+

- Django 4.0+

- Django REST Framework 3.14+

---

## Models

The package provides navigation models based on the following hierarchy:

```text
Menu
SubMenu
Page
Widget
```

Permissions are maintained separately using external identifiers.

For example:

```python
class NavPermission(models.Model):
    id = models.BigAutoField(primary_key=True)

    role_id = models.BigIntegerField(
        db_index=True,
        help_text="External Role ID",
    )

    subrole_id = models.BigIntegerField(
        db_index=True,
        help_text="External SubRole ID",
    )
```

Using external IDs makes the package suitable for applications that already have their own:

- User model

- Role model

- SubRole model

- Authentication system

The package does not require your existing role tables to be directly related through Django foreign keys.

---

## Authentication

The package is designed to work with existing authentication systems.

You can integrate it with:

- JWT/Outh authentication

- Custom JWT authentication

- Django authentication

- Custom `UserMaster`

- External authentication services

For example, if your project already uses a custom user model:

```python
class UserMaster:
    id = ...
    role_id = ...
    subrole_id = ...
```

the navigation package can use those identifiers to determine the user's available navigation.

---

## Permissions

Navigation permissions can be controlled using:

```text
Role
  ↓
SubRole
  ↓
Navigation Permission
  ↓
Menu / SubMenu / Page / Widget
```

This allows different users to receive different navigation structures.

Example:

```text
Admin
 ├── Dashboard
 ├── Reports
 ├── User Management
 └── Settings

Manager
 ├── Dashboard
 └── Reports

Operator
 └── Dashboard
```

The frontend does not need to hardcode these rules.

Instead, it can request the navigation from the backend.

---

## Follow these steps to use this package in your project

## Installation

Install the package using pip:

```bash
pip install drf-dynamic-nav
```

Or with `uv`:

```bash
uv add drf-dynamic-nav
```

Paste the following path in projects [urls.py](http://urls.py) file

```python
path(
        "api/navigation/",
        include("drf_dynamic_nav.urls"),
    ),
```

for example:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        "api/navigation/",
        include("drf_dynamic_nav.urls"),
    ),
]
```

Configuration in [settings.py](http://settings.py) file

## Configuration

Add the application to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",

    # Third-party apps
    "rest_framework",

    # DRF Dynamic Navigation
    "drf_dynamic_nav",
]
```

```python
DYNAMIC_NAV = {
    "NAVIGATION_ITEM_TABLE_NAME": "test_navigation_item",  # if you want to rename the table name
    "NAV_PERMISSION_TABLE_NAME": "test_nav_permission",  # if you want to rename the table name
    "USER_MODEL": "users.UserMaster",   # path of your usermaster table
    "USER_ID_FIELD": "id", # user id primary or unique field of your usermaster table
    "ADMIN_ROLE_IDS": [1], # define admin role ids here for admin only accessible api
}
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

API ENDPOINTS

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/get-nav-permissions/` | Get navigation permissions |
| `POST` | `/permissions/create/` | Create role-based navigation permissions |
| `POST` | `/permissions/update/` | Update role-based navigation permissions |

Admin control only apis

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `GET /get-nav-items/?role_id=1&subrole_id=1` | Get navigation items available for a role/user |
| `POST` | `/nav-items/create/` | Create navigation items |
| `POST` | `/nav-items/update/` | Update navigation items |

For navitems have these following item_type choices

```python
 MENU = "menu", "Menu"
 SUBMENU = "submenu", "SubMenu"
 PAGE = "page", "Page"
 WIDGET = "widget", "Widget"
```

\
\
**CURLS**

> create navigation items (menu, submenu, page, and widgets) data

`curl --location 'http://127.0.0.1:8000/api/navigation/nav-items/create/' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN' \`

`--header 'Content-Type: application/json' \`

`--data '{`

`"name": "User Management",`

`"code": "user_management",`

`"item_type": "menu",`

`"parent_id": 1,`

`"url": null,`

`"icon": "users",`

`"sort_order": 1,`

`"is_active": true,`

`"metadata": {}`

`}'`

**Response:**

`{`

`"is_success": true,`

`"message": "Navigation item created successfully.",`

`"data": {`

`"id": 2,`

`"name": "User Management",`

`"code": "user_management",`

`"item_type": "submenu",`

`"parent_id": 1,`

`"parent_name": "Dashboard",`

`"url": null,`

`"icon": "users",`

`"sort_order": 1,`

`"is_active": true,`

`"metadata": {},`

`"created_at": "2026-09-15T12:28:09.068010Z",`

`"updated_at": "2026-09-15T12:28:09.068010Z"`

`}`

`}`

> Update the navigation items data

`curl --location 'http://127.0.0.1:8000/api/navigation/nav-items/update/' \`

`--header 'Content-Type: application/json' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN' \`

`--data '{`

`"nav_item_id": 1,`

`"name": "Main Dashboard",`

`"code": "main_dashboard",`

`"item_type": "menu",`

`"parent_id": null,`

`"url": null,`

`"icon": "dashboard",`

`"sort_order": 1,`

`"is_active": true,`

`"metadata": {}`

`}'`

Response:

`{`

`"is_success": true,`

`"message": "Navigation item updated successfully.",`

`"data": {`

`"id": 1,`

`"name": "Main Dashboard",`

`"code": "main_dashboard",`

`"item_type": "menu",`

`"parent_id": null,`

`"url": null,`

`"icon": "dashboard",`

`"sort_order": 1,`

`"is_active": true,`

`"metadata": {}`

`}`

`}`

Get active or inactive menu,submenu,pages or widgets based on role or subrole

`curl --location 'http://127.0.0.1:8000/api/navigation/get-role-nav-items/?role_id=1&subrole_id=2&limit=10&offset=0' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN'`

Response:\
`{`

`    "is_success": true,`

`    "message": "Role navigation list fetched successfully.",`

`    "data": {`

`        "role_id": 3,`

`        "subrole_id": 3,`

`        "menus": [`

`            {`

`                "navigation_item_id": 1,`

`                "name": "Main Dashboard",`

`                "code": "main_dashboard",`

`                "item_type": "menu",`

`                "url": null,`

`                "icon": "dashboard",`

`                "sort_order": 1,`

`                "is_active": true,`

`                "permission_active": false,`

`                "permissions": {`

`                    "can_view": false,`

`                    "can_create": false,`

`                    "can_update": false,`

`                    "can_delete": false`

`                },`

`                "children": [`

`                    {`

`                        "navigation_item_id": 2,`

`                        "name": "User Management",`

`                        "code": "user_management",`

`                        "item_type": "submenu",`

`                        "url": null,`

`                        "icon": "users",`

`                        "sort_order": 1,`

`                        "is_active": true,`

`                        "permission_active": false,`

`                        "permissions": {`

`                            "can_view": false,`

`                            "can_create": false,`

`                            "can_update": false,`

`                            "can_delete": false`

`                        },`

`                        "children": []`

`                    }`

`                ]`

`            },`

`            {`

`                "navigation_item_id": 3,`

`                "name": "reports Management",`

`                "code": "reports",`

`                "item_type": "menu",`

`                "url": null,`

`                "icon": "users",`

`                "sort_order": 1,`

`                "is_active": true,`

`                "permission_active": false,`

`                "permissions": {`

`                    "can_view": false,`

`                    "can_create": false,`

`                    "can_update": false,`

`                    "can_delete": false`

`                },`

`                "children": []`

`            }`

`        ]`

`    },`

`    "total_count": 2`

`}`

assign permissions based on role and subrole\
`curl --location 'http://127.0.0.1:8000/api/navigation/permissions/create/' \`

`--header 'Content-Type: application/json' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN' \`

`--data '{`

`    "role_id": 1,`

`    "subrole_id": 1,`

`    "navigation_item_id": 1,`

`    "can_view": true,`

`    "can_create": true,`

`    "can_update": true,`

`    "can_delete": false`

`}'`

Response:

`{`

`    "is_success": true,`

`    "message": "Navigation permission created successfully.",`

`    "data": {`

`        "id": 1,`

`        "role_id": 1,`

`        "subrole_id": 1,`

`        "navigation_item_id": 1,`

`        "navigation_item_name": "Main Dashboard",`

`        "navigation_item_code": "main_dashboard",`

`        "permissions": {`

`            "can_view": true,`

`            "can_create": true,`

`            "can_update": true,`

`            "can_delete": false`

`        }`

`    }`

`}`

update permissions based on role and subrole

`curl --location 'http://127.0.0.1:8000/api/navigation/permissions/update/' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN' \`

`--header 'Content-Type: application/json' \`

`--data '{`

`    "role_id": 1,`

`    "subrole_id": 1,`

`    "permissions": [`

`        {`

`            "navigation_item_id": 1,`

`            "can_view": true,`

`            "can_create": true,`

`            "can_update":true,`

`            "can_delete": true`

`        },`

`        {`

`            "navigation_item_id": 2,`

`            "can_view": true,`

`            "can_create": true,`

`            "can_update": false,`

`            "can_delete": true`

`        }`

`    ]`

`}'`

Response:

`{`

`    "is_success": true,`

`    "message": "Role navigation permissions updated successfully.",`

`    "data": {`

`        "role_id": 1,`

`        "subrole_id": 1,`

`        "deleted_permissions": 1,`

`        "created_permissions": 2,`

`        "permissions": [`

`            {`

`                "id": 4,`

`                "navigation_item_id": 1,`

`                "navigation_item_name": "Main Dashboard",`

`                "navigation_item_code": "main_dashboard",`

`                "item_type": "menu",`

`                "permissions": {`

`                    "can_view": true,`

`                    "can_create": true,`

`                    "can_update": true,`

`                    "can_delete": true`

`                }`

`            },`

`            {`

`                "id": 5,`

`                "navigation_item_id": 2,`

`                "navigation_item_name": "User Management",`

`                "navigation_item_code": "user_management",`

`                "item_type": "submenu",`

`                "permissions": {`

`                    "can_view": true,`

`                    "can_create": true,`

`                    "can_update": false,`

`                    "can_delete": true`

`                }`

`            }`

`        ]`

`    }`

`}`

Get navigation permissions based on role or subrole 

<span style="color: rgb(229, 87, 87);">note: call this api after login api</span>

`curl --location 'http://127.0.0.1:8000/api/navigation/get-nav-permissions/' \`

`--header 'Authorization: Bearer YOUR_JWT_TOKEN'`

Response:

`{`

`    "is_success": true,`

`    "message": "Navigation permissions fetched successfully.",`

`    "data": [`

`        {`

`            "role_id": 1,`

`            "subrole_id": 1,`

`            "nav_item_id": 1,`

`            "nav_item_name": "Main Dashboard",`

`            "nav_item_code": "main_dashboard",`

`            "item_type": "menu",`

`            "url": null,`

`            "icon": "dashboard",`

`            "sort_order": 1,`

`            "permissions": {`

`                "can_view": true,`

`                "can_create": true,`

`                "can_update": true,`

`                "can_delete": true`

`            },`

`            "children": [`

`                {`

`                    "role_id": 1,`

`                    "subrole_id": 1,`

`                    "nav_item_id": 2,`

`                    "nav_item_name": "User Management",`

`                    "nav_item_code": "user_management",`

`                    "item_type": "submenu",`

`                    "url": null,`

`                    "icon": "users",`

`                    "sort_order": 1,`

`                    "permissions": {`

`                        "can_view": true,`

`                        "can_create": true,`

`                        "can_update": false,`

`                        "can_delete": true`

`                    },`

`                    "children": []`

`                }`

`            ]`

`        }`

`    ]`

`}`
