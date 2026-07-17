from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accounts.models import User
    from departments.models import Department, DepartmentPermission


class DepartmentPermissionsService:
    """Primitive class to check if User is owner or holds a DepartmentPermission codename
    on this specific department. Should only be called from higher level
    services that have already verified an authenticated user."""

    @classmethod
    def has_permission(
        cls, user: User, department: Department, codename: DepartmentPermission
    ) -> bool:
        if department.check_if_owned_by_user(user):
            return True
        return user.has_perm(f"departments.{codename}", department)
