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
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_true_for_member_of_editor_department_with_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_EDIT_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_true_for_department_owner_of_an_editor_department(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(
            FormDefinitionPermissionsService.has_editor_permission(
                owner, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_false_for_department_member_without_the_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_false_for_capability_grant_without_membership(self) -> None:
        # Membership is a floor, same as FormAccessService.can_create_form —
        # an editor_department grant without membership in it isn't enough.
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_permissions=[(user, DepartmentPermission.CAN_EDIT_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_false_for_unrelated_user(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )

    def test_editor_department_does_not_imply_a_different_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_CREATE_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(
            FormDefinitionPermissionsService.has_editor_permission(
                user, form_def, DepartmentPermission.CAN_EDIT_FORMS
            )
        )
