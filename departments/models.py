from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from treebeard.mp_tree import MP_Node

if TYPE_CHECKING:
    from accounts.models import User


class DepartmentHasChildrenError(Exception):
    """Raised by Department.archive() when the department still has child
    departments — the caller must move or archive them first."""


class DepartmentPermission(StrEnum):
    """Codenames for the six department-scoped guardian permissions on
    Department (Meta.permissions, below). Only CAN_CREATE_FORMS is wired up
    to a check/grant flow so far — the rest are declared here so the schema
    lands once, but nothing outside this enum references them yet."""

    CAN_CREATE_FORMS = "can_create_forms"
    CAN_EDIT_FORMS = "can_edit_forms"
    CAN_ARCHIVE_FORMS = "can_archive_forms"
    CAN_CREATE_WORKFLOWS = "can_create_workflows"
    CAN_EDIT_WORKFLOWS = "can_edit_workflows"
    CAN_ARCHIVE_WORKFLOWS = "can_archive_workflows"


class Department(MP_Node):
    name = models.CharField(max_length=100, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, editable=False)
    owners: models.ManyToManyField[User, Any] = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="owned_departments",
        blank=True,
    )
    is_archived = models.BooleanField(default=False)

    node_order_by = ["name"]

    class Meta:
        permissions = [
            (
                DepartmentPermission.CAN_CREATE_FORMS,
                "Can create forms for this department",
            ),
            (DepartmentPermission.CAN_EDIT_FORMS, "Can edit this department's forms"),
            (
                DepartmentPermission.CAN_ARCHIVE_FORMS,
                "Can archive this department's forms",
            ),
            (
                DepartmentPermission.CAN_CREATE_WORKFLOWS,
                "Can create workflows for this department's forms",
            ),
            (
                DepartmentPermission.CAN_EDIT_WORKFLOWS,
                "Can edit this department's workflows",
            ),
            (
                DepartmentPermission.CAN_ARCHIVE_WORKFLOWS,
                "Can archive this department's workflows",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def group_name(self) -> str:
        return f"dept-{self.name}"

    def sync_group_name(self) -> None:
        """Ensures this department has a Group whose name matches
        group_name — creates the Group if one doesn't exist yet, or
        updates and persists its name if it's drifted (e.g. after a
        rename). Safe to call whether or not self.group exists."""
        if not self.group_id:
            self.group = Group.objects.create(name=self.group_name)
        elif self.group.name != self.group_name:
            self.group.name = self.group_name
            self.group.save()

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.sync_group_name()
        super().save(*args, **kwargs)

    def add_member(self, user: User) -> None:
        self.group.user_set.add(user)

    def remove_member(self, user: User) -> None:
        self.group.user_set.remove(user)

    def add_user_to_owners(self, user: User) -> None:
        self.owners.add(user)

    def remove_user_from_owners(self, user: User) -> None:
        self.owners.remove(user)

    def check_if_owned_by_user(self, user: User) -> bool:
        return user in self.owners.all()

    @classmethod
    def get_departments_owned_by_user(cls, user: User) -> models.QuerySet[Department]:
        """Departments this user directly owns, plus every descendant of
        each — owning a department implies owning its sub-departments
        too, consistent with how department scoping works everywhere
        else in this project (e.g. FormPermissions flattening)."""
        department_ids = set()
        for department in user.owned_departments.all():
            department_ids.add(department.pk)
            department_ids.update(
                department.get_descendants().values_list("pk", flat=True)
            )
        return cls.objects.filter(pk__in=department_ids)

    def archive(self) -> None:
        """Archives this department. Raises DepartmentHasChildrenError if it
        still has any child departments — move or archive them first."""
        if self.get_children().exists():
            raise DepartmentHasChildrenError(
                f'"{self.name}" still has child departments; move or archive '
                "them before archiving this department."
            )
        self.is_archived = True
        self.save()


@receiver(pre_delete, sender=Department)
def prevent_department_deletion(
    sender: type[Department], instance: Department, **kwargs: Any
) -> None:
    raise PermissionError(
        "Departments cannot be deleted; call archive() instead to preserve "
        "audit history."
    )
