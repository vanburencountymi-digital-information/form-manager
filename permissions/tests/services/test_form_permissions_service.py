from django.test import TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentUserFactory
from permissions.services.form_permissions_service import FormPermissionsService
from permissions.tests.factories import FormPermissionsFactory


class FormPermissionsServiceHasEditorPermissionTests(TestCase):
    def test_true_for_direct_editor_user_grant(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_users=[user])
        self.assertTrue(FormPermissionsService.has_editor_permission(user, form_def))

    def test_true_for_member_of_editor_department_with_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(FormPermissionsService.has_editor_permission(user, form_def))

    def test_true_for_department_owner_of_an_editor_department(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(FormPermissionsService.has_editor_permission(owner, form_def))

    def test_true_for_owner_of_an_ancestor_of_an_editor_department(self) -> None:
        parent = DepartmentUserFactory(name="Engineering")
        child = DepartmentUserFactory(name="Backend", parent=parent)
        owner = UserFactory()
        parent.add_user_to_owners(owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[child])
        self.assertTrue(FormPermissionsService.has_editor_permission(owner, form_def))

    def test_false_for_department_member_without_the_capability(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(FormPermissionsService.has_editor_permission(user, form_def))

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
        self.assertFalse(FormPermissionsService.has_editor_permission(user, form_def))

    def test_workflow_grant_does_not_satisfy_the_forms_capability(self) -> None:
        # has_editor_permission is hardcoded to CAN_MANAGE_FORMS — a grant
        # on the other axis (workflows) shouldn't satisfy it.
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_WORKFLOWS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertFalse(FormPermissionsService.has_editor_permission(user, form_def))


class FormPermissionsServiceApplySubmissionViewerPermissionsTests(TestCase):
    # Group membership is checked by pk, not instance equality, throughout
    # this class — reviewer_groups/admin_groups are ManyToManyField(Group),
    # so .all() returns plain Group rows; a PersonalGroup instance never
    # equals a Group instance even for the same underlying row, since
    # Django's model equality also checks _meta.concrete_model
    # (multi-table inheritance).

    def test_adds_each_viewer_users_personal_group_to_reviewer_groups(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice, bob])
        FormPermissionsService.apply_submission_viewer_permissions(fp)
        reviewer_group_pks = fp.form.reviewer_groups.values_list("pk", flat=True)
        self.assertIn(alice.personal_group.pk, reviewer_group_pks)
        self.assertIn(bob.personal_group.pk, reviewer_group_pks)

    def test_does_not_touch_admin_groups(self) -> None:
        # reviewer_groups only — admin_groups additionally grants acting on
        # behalf of an approval assignee, a write capability
        # submission_viewer_users must never carry (see
        # apply_submission_viewer_permissions docstring).
        alice = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice])
        FormPermissionsService.apply_submission_viewer_permissions(fp)
        admin_group_pks = fp.form.admin_groups.values_list("pk", flat=True)
        self.assertNotIn(alice.personal_group.pk, admin_group_pks)

    def test_removing_a_viewer_user_and_reapplying_removes_their_group(self) -> None:
        alice = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice])
        FormPermissionsService.apply_submission_viewer_permissions(fp)
        fp.submission_viewer_users.remove(alice)
        FormPermissionsService.apply_submission_viewer_permissions(fp)
        reviewer_group_pks = fp.form.reviewer_groups.values_list("pk", flat=True)
        self.assertNotIn(alice.personal_group.pk, reviewer_group_pks)

    def test_no_viewer_users_clears_reviewer_groups(self) -> None:
        form_def = FormDefinitionFactory()
        alice = UserFactory()
        form_def.reviewer_groups.add(alice.personal_group)
        fp = FormPermissionsFactory(form=form_def)
        FormPermissionsService.apply_submission_viewer_permissions(fp)
        self.assertEqual(form_def.reviewer_groups.count(), 0)
