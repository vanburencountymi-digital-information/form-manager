from __future__ import annotations

from typing import TYPE_CHECKING

from guardian.shortcuts import get_objects_for_user

from departments.models import Department, DepartmentPermission
from permissions.guards import (
    assert_authenticated_user,
    is_authenticated_user,
    return_false_if_user_not_authenticated,
)
from permissions.services.admin_group_service import AdministratorGroupService
from permissions.services.department_perm_service import DepartmentPermissionsService
from permissions.services.form_def_perm_service import FormDefinitionPermissionsService

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser
    from django.db.models import QuerySet
    from django_forms_workflows.models import FormDefinition

    from accounts.models import User


class FormAccessService:
    """A high-level service class that checks user privileges down a
    chain to verify access for communication with views.

    For each method, runs the following checks in order and returns
    immediately if check passes:
    - check if user exists and is authenticated
    - check if user is admin
    - if relevant, check if user is owner of this department or a parent department.
    - if relevant, check if user has department-scoped permissions.
    - if relevant, check if user has permissions granted on FormDef
    """

    @classmethod
    @return_false_if_user_not_authenticated
    def can_create_form(
        cls, user: User | AnonymousUser | None, department: Department
    ) -> bool:
        """True if user is administrator, an owner of this department
        or a parent department, or if they've been granted this
        department level permission."""
        user = assert_authenticated_user(user)
        if AdministratorGroupService.is_administrator(user):
            return True
        if department.check_if_owned_by_user(user):
            return True
        return DepartmentPermissionsService.has_permission(
            user, department, DepartmentPermission.CAN_MANAGE_FORMS
        )

    @classmethod
    @return_false_if_user_not_authenticated
    def can_manage_form(
        cls, user: User | AnonymousUser | None, form_def: FormDefinition
    ) -> bool:
        """True if user can edit or archive form_def's schema — mirrors
        can_create_form's shape: administrator bypass, then ownership
        (including cascaded ownership of an ancestor) of one of
        form_def's editor_departments, then the editor-grant check
        (direct editor_users grant, or an explicit can_manage_forms
        grant on one of editor_departments)."""
        user = assert_authenticated_user(user)
        if AdministratorGroupService.is_administrator(user):
            return True
        if any(
            department.check_if_owned_by_user(user)
            for department in form_def.permissions.editor_departments.all()
        ):
            return True
        return FormDefinitionPermissionsService.has_editor_permission(
            user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
        )

    @classmethod
    def get_creatable_departments(
        cls, user: User | AnonymousUser | None
    ) -> QuerySet[Department]:
        """Departments this user could scope a brand new form to."""

        if not is_authenticated_user(user):
            return Department.objects.none()

        if AdministratorGroupService.is_administrator(user):
            return Department.objects.filter(is_archived=False)

        granted_department_ids = get_objects_for_user(
            user,
            f"departments.{DepartmentPermission.CAN_MANAGE_FORMS}",
            klass=Department,
        ).values_list("pk", flat=True)

        owned_department_ids = Department.get_departments_owned_by_user(
            user
        ).values_list("pk", flat=True)

        creatable_ids = set(owned_department_ids | granted_department_ids)
        return Department.objects.filter(pk__in=creatable_ids, is_archived=False)

    # No separate can_archive_form/can_create_form-for-existing-form —
    # can_manage_form already covers editing and archiving both, since
    # they share the same CAN_MANAGE_FORMS capability; a distinct method
    # would just be a duplicate of the one above.
    #
    # Workflows aren't wired up yet, but will follow the identical shape
    # once built — a single can_manage_workflow(user, form_def) checking
    # DepartmentPermission.CAN_MANAGE_WORKFLOWS via
    # FormDefinitionPermissionsService.has_editor_permission, covering
    # create/edit/archive together, same reasoning as the forms axis.
