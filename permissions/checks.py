from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.admin_group_service import AdministratorGroupService

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User


def is_authenticated_user(user: User | AnonymousUser | None) -> bool:
    if not user:
        return False
    return user.is_authenticated


def is_a_department_owner(user: User | AnonymousUser | None) -> bool:
    """True if user directly owns at least one department. Guards against
    AnonymousUser explicitly."""
    if not user:
        return False
    if not user.is_authenticated:
        return False
    return user.owned_departments.exists()


def is_administrator(user: User | AnonymousUser | None) -> bool:
    """Utility method for AdministratorGroupService.is_administrator."""
    return AdministratorGroupService.is_administrator(user)


def can_create_forms(user: User | AnonymousUser | None) -> bool:
    """True if user can create at least one form somewhere"""
    # TODO: update once there are department level permissions
    return is_administrator(user) or is_a_department_owner(user)


def can_edit_forms(user: User | AnonymousUser | None) -> bool:
    """True if user can edit at least one form somewhere"""
    # TODO: update once there are department level permissions
    return is_administrator(user) or is_a_department_owner(user)
