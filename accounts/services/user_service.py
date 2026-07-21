from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import transaction

from accounts.models import PersonalGroup, User
from departments.models import DepartmentPermission
from permissions.services.admin_group_service import AdministratorGroupService
from permissions.services.department_perm_service import DepartmentPermissionsService

if TYPE_CHECKING:
    from departments.models import Department


class UserService:
    """Manage Users, including creation:
    `create_user()`: grants all necessary permissions, departments, and groups atomically."""

    @classmethod
    @transaction.atomic
    def create_user(
        cls,
        *,
        email: str,
        first_name: str,
        last_name: str,
        department: Department,
        is_department_owner: bool = False,
        can_create_forms: bool = False,
        is_administrator: bool = False,
    ) -> User:
        """
        Creates User object with an unusable password, their PersonalGroup, and adds them to their Department.

        Optional:
        -add user to department owners
        -add user to AdministratorGroup
        -assign user department-scoped permissions.
        """
        user = User(email=email, first_name=first_name, last_name=last_name)
        user.set_unusable_password()
        user.save()

        personal_group = PersonalGroup.objects.create(owner=user)
        user.groups.add(personal_group)
        department.add_member(user)

        if is_department_owner:
            department.add_user_to_owners(user)

        if can_create_forms:
            DepartmentPermissionsService.grant_permission(
                user, department, DepartmentPermission.CAN_CREATE_FORMS
            )

        if is_administrator:
            AdministratorGroupService.add_administrator(user)

        return user
