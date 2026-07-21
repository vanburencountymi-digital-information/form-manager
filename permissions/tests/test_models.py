from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.tests.factories import DepartmentFactory
from permissions.models import apply_form_permissions
from permissions.tests.factories import FormPermissionsFactory


class FormPermissionsTests(TestCase):
    def test_created_with_no_departments_or_users_by_default(self) -> None:
        fp = FormPermissionsFactory()
        self.assertEqual(fp.editor_departments.count(), 0)
        self.assertEqual(fp.editor_users.count(), 0)
        self.assertEqual(fp.submission_viewer_users.count(), 0)

    def test_can_assign_editor_departments(self) -> None:
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        fp = FormPermissionsFactory(editor_departments=[eng, sales])
        self.assertEqual(fp.editor_departments.count(), 2)
        self.assertIn(eng, fp.editor_departments.all())
        self.assertIn(sales, fp.editor_departments.all())

    def test_can_assign_editor_users(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(editor_users=[alice, bob])
        self.assertEqual(fp.editor_users.count(), 2)
        self.assertIn(alice, fp.editor_users.all())
        self.assertIn(bob, fp.editor_users.all())

    def test_can_assign_submission_viewer_users(self) -> None:
        carol = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[carol])
        self.assertEqual(fp.submission_viewer_users.count(), 1)
        self.assertIn(carol, fp.submission_viewer_users.all())

    def test_editor_and_submission_viewer_users_are_independent(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(editor_users=[alice], submission_viewer_users=[bob])
        self.assertIn(alice, fp.editor_users.all())
        self.assertNotIn(alice, fp.submission_viewer_users.all())
        self.assertIn(bob, fp.submission_viewer_users.all())
        self.assertNotIn(bob, fp.editor_users.all())

    def test_a_user_can_be_both_editor_and_viewer(self) -> None:
        user = UserFactory()
        fp = FormPermissionsFactory(editor_users=[user], submission_viewer_users=[user])
        self.assertIn(user, fp.editor_users.all())
        self.assertIn(user, fp.submission_viewer_users.all())

    def test_a_form_can_only_have_one_form_permissions_row(self) -> None:
        fp = FormPermissionsFactory()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FormPermissionsFactory(form=fp.form)


class ApplyFormPermissionsTests(TestCase):
    def test_adds_each_viewer_users_personal_group_to_reviewer_groups(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice, bob])
        apply_form_permissions(fp)
        reviewer_groups = fp.form.reviewer_groups.all()
        self.assertIn(alice.personal_group, reviewer_groups)
        self.assertIn(bob.personal_group, reviewer_groups)

    def test_does_not_touch_admin_groups(self) -> None:
        # reviewer_groups only — admin_groups additionally grants acting on
        # behalf of an approval assignee, a write capability
        # submission_viewer_users must never carry (see apply_form_permissions
        # docstring).
        alice = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice])
        apply_form_permissions(fp)
        self.assertNotIn(alice.personal_group, fp.form.admin_groups.all())

    def test_removing_a_viewer_user_and_reapplying_removes_their_group(self) -> None:
        alice = UserFactory()
        fp = FormPermissionsFactory(submission_viewer_users=[alice])
        apply_form_permissions(fp)
        fp.submission_viewer_users.remove(alice)
        apply_form_permissions(fp)
        self.assertNotIn(alice.personal_group, fp.form.reviewer_groups.all())

    def test_no_viewer_users_clears_reviewer_groups(self) -> None:
        form_def = FormDefinitionFactory()
        alice = UserFactory()
        form_def.reviewer_groups.add(alice.personal_group)
        fp = FormPermissionsFactory(form=form_def)
        apply_form_permissions(fp)
        self.assertEqual(form_def.reviewer_groups.count(), 0)
