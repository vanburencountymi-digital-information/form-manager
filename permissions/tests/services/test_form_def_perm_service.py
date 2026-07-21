from django.test import TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentUserFactory
from permissions.services.form_def_perm_service import FormDefinitionPermissionsService
from permissions.tests.factories import FormPermissionsFactory


class FormDefinitionPermissionsServiceHasEditorPermissionTests(TestCase):
    def test_true_for_direct_editor_user_grant(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_users=[user])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    def test_true_for_member_of_editor_department_with_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    def test_true_for_department_owner_of_an_editor_department(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                owner, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    def test_true_for_owner_of_an_ancestor_of_an_editor_department(self) -> None:
        parent = DepartmentUserFactory(name="Engineering")
        child = DepartmentUserFactory(name="Backend", parent=parent)
        owner = UserFactory()
        parent.add_user_to_owners(owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[child])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                owner, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    def test_false_for_department_member_without_the_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    # No test for "capability grant without membership" here —
    # DepartmentPermissionsService.grant_permission now enforces membership
    # at write-time (raises UserNotAMemberError otherwise), and
    # Department.remove_member revokes the grant if membership is later
    # removed — so any existing grant already implies current membership.
    # Constructing that state directly via guardian's assign_perm
    # (bypassing the service) is an intentionally-unsupported shortcut.

    def test_false_for_unrelated_user(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )

    def test_editor_department_does_not_imply_a_different_capability(self) -> None:
        # A grant on a different axis (workflows) shouldn't satisfy a
        # forms-capability check.
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_WORKFLOWS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_MANAGE_FORMS
            )
        )
