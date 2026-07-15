from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import Group, Permission
from django.db import models

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User
    from departments.models import Department


class AdministratorPermission(StrEnum):
    """Canonical definition of each codename, referenced by both
    AdministratorPermissions.Meta.permissions and PERMISSION_CODENAMES."""

    CAN_INVITE_TO_ANY_DEPARTMENT = "can_invite_to_any_department"
    CAN_EDIT_ANY_FORM = "can_edit_any_form"


class AdministratorPermissions(models.Model):
    """A semi-abstract model (no rows created) to provide a single
    home for admin related permissions."""

    # Don't register in Admin; Roles are managed via Groups

    GROUP_NAME = "Administrator"
    PERMISSION_CODENAMES = [permission.value for permission in AdministratorPermission]

    class Meta:
        permissions = [
            (
                AdministratorPermission.CAN_INVITE_TO_ANY_DEPARTMENT,
                "Can invite users to any department",
            ),
            (
                AdministratorPermission.CAN_EDIT_ANY_FORM,
                "Can edit any form, bypassing department-level form scoping.",
            ),
        ]

    def __str__(self) -> str:
        return "admin_permissions"

    @classmethod
    def sync_permissions(cls) -> Group:
        """Sets the Administrator group's permissions, creating the group first
        if it doesn't."""
        group, _ = Group.objects.get_or_create(name=cls.GROUP_NAME)
        group.permissions.set(
            Permission.objects.filter(codename__in=cls.PERMISSION_CODENAMES)
        )
        return group

    @classmethod
    def get_or_create_group(cls) -> Group:
        """Ensures the Administrator group exists and syncs permissions
        on creation."""
        group, created = Group.objects.get_or_create(name=cls.GROUP_NAME)
        if created:
            cls.sync_permissions()
        return group

    @classmethod
    def is_administrator(cls, user: User | AnonymousUser | None) -> bool:
        """Checks if user belongs to the Administrator group. Returns `False`
        if no user."""
        if user:
            group = cls.get_or_create_group()
            return user.groups.filter(pk=group.pk).exists()
        return False


class FormPermissions(models.Model):
    """Sets FormDefinition permissions.
    `editor_departments`: Who can edit the form schema.
    `viewer_departments`: Who can view for the form submissions."""

    form = models.OneToOneField(
        "django_forms_workflows.FormDefinition",
        on_delete=models.CASCADE,
        related_name="permissions",
    )

    def __str__(self) -> str:
        return f"{self.form.name} permissions"

    editor_departments: models.ManyToManyField[Department, Any] = (
        models.ManyToManyField(
            "departments.Department",
            related_name="editable_forms",
            blank=True,
            help_text=(
                "Departments whose members can edit this form's structure "
                "(fields, workflow, settings) in the visual builder. Does not "
                "affect who can submit the form or view its responses."
            ),
        )
    )
    viewer_departments: models.ManyToManyField[Department, Any] = (
        models.ManyToManyField(
            "departments.Department",
            related_name="viewable_forms",
            blank=True,
            help_text=(
                "Departments whose members can view every submission to this "
                "form, at any time — independent of whether they're an "
                "assigned approver on any specific workflow stage. Does not "
                "grant edit access to the form itself."
            ),
        )
    )
