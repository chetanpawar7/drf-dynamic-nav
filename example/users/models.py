from django.db import models


class RoleMaster(models.Model):
    id = models.BigAutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "role_master"
        ordering = ["id"]

    def __str__(self):
        return self.name


class SubRoleMaster(models.Model):
    id = models.BigAutoField(primary_key=True)

    role = models.ForeignKey(
        RoleMaster,
        on_delete=models.CASCADE,
        related_name="subroles",
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "subrole_master"
        ordering = ["id"]


    def __str__(self):
        return f"{self.role.name} - {self.name}"


class UserMaster(models.Model):
    id = models.BigAutoField(primary_key=True)

    username = models.CharField(
        max_length=100,
        unique=True,
    )

    role = models.ForeignKey(
        RoleMaster,
        on_delete=models.PROTECT,
        related_name="users",
    )

    subrole = models.ForeignKey(
        SubRoleMaster,
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.username