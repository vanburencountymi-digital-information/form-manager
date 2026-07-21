from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.services.department_perm_service import DepartmentPermissionsService

if TYPE_CHECKING:
    from django_forms_workflows.models import FormDefinition

    from accounts.models import User
    from departments.models import DepartmentPermission


class FormDefinitionPermissionsService:
    """Primitive: does user hold editor-level access to form_def, via
    FormPermissions' editor axis? No auth guard, no admin bypass — trust
    the composite (FormAccessService) already checked both."""

    @classmethod
    def has_editor_permission(
        cls, user: User, form_def: FormDefinition, codename: DepartmentPermission
    ) -> bool:
        """True if user is a direct editor_users grant on form_def, or
        holds `codename` (an explicit guardian grant) on one of its
        editor_departments. Ownership is checked by the composite
        (FormAccessService.can_manage_form) before this primitive is
        ever called — mirrors how FormAccessService.can_create_form
        checks ownership itself before calling
        DepartmentPermissionsService.has_permission. No separate
        membership check needed either: grant_permission already
        requires membership at write-time, and Department.remove_member
        revokes the grant if membership is later removed — so any
        existing grant already implies current membership."""
        permissions = form_def.permissions
        if permissions.editor_users.filter(pk=user.pk).exists():
            return True
        for department in permissions.editor_departments.all():
            if DepartmentPermissionsService.has_permission(user, department, codename):
                return True
        return False
