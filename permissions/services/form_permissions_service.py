from __future__ import annotations

from typing import TYPE_CHECKING

from departments.models import DepartmentPermission
from permissions.models import FormPermissions
from permissions.services.department_perm_service import DepartmentPermissionsService

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django_forms_workflows.models import FormDefinition

    from accounts.models import User
    from departments.models import Department


class FormPermissionsService:
    """Checks and manages permissions held on the FormPermissions object."""

    @classmethod
    def create_form_permissions(
        cls,
        form_def: FormDefinition,
        editor_departments: Iterable[Department],
        editor_users: Iterable[User],
        submission_viewer_users: Iterable[User],
    ) -> FormPermissions:
        """Create FormDef permissions row, then update permissions."""
        form_permissions = FormPermissions.objects.create(form=form_def)
        return cls.update_form_permissions(
            form_permissions, editor_departments, editor_users, submission_viewer_users
        )

    @classmethod
    def update_form_permissions(
        cls,
        form_permissions: FormPermissions,
        editor_departments: Iterable[Department],
        editor_users: Iterable[User],
        submission_viewer_users: Iterable[User],
    ) -> FormPermissions:
        """Sets form_permissions' three scoping fields and immediately
        applies the viewer-axis flattening (see
        apply_submission_viewer_permissions) — so reviewer_groups
        reflect submission_viewer_users right away, not just after the
        next unrelated change. Shared by create_form_permissions (right
        after creating the row) and the edit flow (after validating
        changes to an existing row)."""
        form_permissions.editor_departments.set(editor_departments)
        form_permissions.editor_users.set(editor_users)
        form_permissions.submission_viewer_users.set(submission_viewer_users)
        cls.apply_submission_viewer_permissions(form_permissions)
        return form_permissions

    @classmethod
    def has_editor_permission(cls, user: User, form_def: FormDefinition) -> bool:
        """Checks if the user is in the editor permissions explicitly
        granted on the FormPermissions object associated with FormDef."""

        permissions = form_def.permissions

        if permissions.editor_users.filter(pk=user.pk).exists():
            return True

        for department in permissions.editor_departments.all():
            if DepartmentPermissionsService.has_permission(
                user, department, DepartmentPermission.CAN_MANAGE_FORMS
            ):
                return True

        return False

    @classmethod
    def apply_submission_viewer_permissions(
        cls, form_permissions: FormPermissions
    ) -> None:
        """Django-forms-workflows uses FormDef.reviewer_groups to grant read access to form submissions.
        This method synchronizes FormDef.reviewer_groups with the FormPermission `submission_viewer_users` object, allowing for granular, per-User control of who can view form submissions."""
        # submission_viewers is treated as source of truth.
        personal_groups = {
            user.personal_group
            for user in form_permissions.submission_viewer_users.all()
        }
        # Synchronize the reviewer_groups on the FormDef with the associated FormPermission `submission_viewer_users`.
        form_permissions.form.reviewer_groups.set(personal_groups)
