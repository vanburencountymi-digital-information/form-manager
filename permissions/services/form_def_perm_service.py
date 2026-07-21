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
        """True if user is a direct editor_users grant on form_def, or a
        member of one of its editor_departments who also holds `codename`
        on that department. Membership is a floor, same as
        FormAccessService.can_create_form — an editor_department grant
        without membership in it isn't enough."""
        permissions = form_def.permissions
        if permissions.editor_users.filter(pk=user.pk).exists():
            return True
        for department in permissions.editor_departments.all():
            if not department.check_if_user_is_member(user):
                continue
            if DepartmentPermissionsService.has_permission(user, department, codename):
                return True
        return False
