from __future__ import annotations

from typing import TYPE_CHECKING

from guardian.shortcuts import get_objects_for_user

from departments.models import Department

if TYPE_CHECKING:
    from accounts.models import User
    from departments.models import DepartmentPermission


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

    @classmethod
    def has_permission_anywhere(
        cls, user: User, codename: DepartmentPermission
    ) -> bool:
        """True if user holds `codename` (an explicit guardian grant) on at
        least one department — ownership is a separate axis, not checked
        here; pair with Department.get_departments_owned_by_user for that."""
        return get_objects_for_user(
            user, f"departments.{codename}", klass=Department
        ).exists()
