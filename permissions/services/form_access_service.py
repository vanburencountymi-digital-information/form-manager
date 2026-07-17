from __future__ import annotations

from typing import TYPE_CHECKING

from departments.models import DepartmentPermission
from permissions.guards import (
    assert_authenticated_user,
    return_false_if_user_not_authenticated,
)
from permissions.services.admin_group_service import AdministratorGroupService
from permissions.services.department_perm_service import DepartmentPermissionsService

# from permissions.services.form_def_perm_service import FormDefinitionPermissionsService

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User
    from departments.models import Department

    # from django_forms_workflows.models import FormDefinition


class FormAccessService:
    """A high-level service class that checks user privileges down a
    chain to verify access for communication with views.

    For each method, runs the following checks in order and returns
    immediately if check passes:
    - check if user exists and is authenticated
    - check if user is admin
    - check if user has department-scoped permissions
    - check if user has individually granted permissions on FormDef, if
    applicable
    """

    @classmethod
    @return_false_if_user_not_authenticated
    def can_create_form(
        cls, user: User | AnonymousUser | None, department: Department
    ) -> bool:
        """True if user can create a new form scoped to `department` —
        administrator, department owner, or explicit can_create_forms grant."""
        user = assert_authenticated_user(user)
        if AdministratorGroupService.is_administrator(user):
            return True
        return DepartmentPermissionsService.has_permission(
            user, department, DepartmentPermission.CAN_CREATE_FORMS
        )

    # --- Everything below depends on FormPermissions.editor_users/
    # viewer_users (not built yet) and FormDefinitionPermissionsService.
    # has_editor_permission (not built yet). Commented out until those land
    # — uncomment one method at a time, alongside its own tests and its own
    # invite-flow wiring (see accounts/forms.py, accounts/views.py).

    # @classmethod
    # @return_false_if_user_not_authenticated
    # def can_edit_form(
    #     cls, user: User | AnonymousUser | None, form_def: FormDefinition
    # ) -> bool:
    #     if AdministratorGroupService.is_administrator(user):
    #         return True
    #     return FormDefinitionPermissionsService.has_editor_permission(
    #         user, form_def, DepartmentPermission.CAN_EDIT_FORMS
    #     )

    # @classmethod
    # @return_false_if_user_not_authenticated
    # def can_archive_form(
    #     cls, user: User | AnonymousUser | None, form_def: FormDefinition
    # ) -> bool:
    #     if AdministratorGroupService.is_administrator(user):
    #         return True
    #     return FormDefinitionPermissionsService.has_editor_permission(
    #         user, form_def, DepartmentPermission.CAN_ARCHIVE_FORMS
    #     )

    # @classmethod
    # @return_false_if_user_not_authenticated
    # def can_create_workflow(
    #     cls, user: User | AnonymousUser | None, form_def: FormDefinition
    # ) -> bool:
    #     if AdministratorGroupService.is_administrator(user):
    #         return True
    #     return FormDefinitionPermissionsService.has_editor_permission(
    #         user, form_def, DepartmentPermission.CAN_CREATE_WORKFLOWS
    #     )

    # @classmethod
    # @return_false_if_user_not_authenticated
    # def can_edit_workflow(
    #     cls, user: User | AnonymousUser | None, form_def: FormDefinition
    # ) -> bool:
    #     if AdministratorGroupService.is_administrator(user):
    #         return True
    #     return FormDefinitionPermissionsService.has_editor_permission(
    #         user, form_def, DepartmentPermission.CAN_EDIT_WORKFLOWS
    #     )

    # @classmethod
    # @return_false_if_user_not_authenticated
    # def can_archive_workflow(
    #     cls, user: User | AnonymousUser | None, form_def: FormDefinition
    # ) -> bool:
    #     if AdministratorGroupService.is_administrator(user):
    #         return True
    #     return FormDefinitionPermissionsService.has_editor_permission(
    #         user, form_def, DepartmentPermission.CAN_ARCHIVE_WORKFLOWS
    #     )
