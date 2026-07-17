from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.guards import require_authenticated_user
from permissions.services.admin_group_service import AdministratorGroupService

if TYPE_CHECKING:
    from accounts.models import User


@require_authenticated_user
def is_a_department_owner(user: User) -> bool:
    """True if user directly owns at least one department."""
    return user.owned_departments.exists()


@require_authenticated_user
def is_administrator(user: User) -> bool:
    """Utility method for AdministratorGroupService.is_administrator."""
    return AdministratorGroupService.is_administrator(user)


@require_authenticated_user
def can_create_forms(user: User) -> bool:
    """True if user can create at least one form somewhere"""
    # TODO: update once there are department level permissions
    return is_administrator(user) or is_a_department_owner(user)


@require_authenticated_user
def can_edit_forms(user: User) -> bool:
    """True if user can edit at least one form somewhere"""
    # TODO: update once there are department level permissions
    return is_administrator(user) or is_a_department_owner(user)
