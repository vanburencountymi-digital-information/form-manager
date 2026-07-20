from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions.tests.factories import FormPermissionsFactory


class FormPermissionsTests(TestCase):
    def test_created_with_no_departments_or_users_by_default(self) -> None:
        fp = FormPermissionsFactory()
        self.assertEqual(fp.editor_departments.count(), 0)
        self.assertEqual(fp.editor_users.count(), 0)
        self.assertEqual(fp.viewer_departments.count(), 0)
        self.assertEqual(fp.viewer_users.count(), 0)

    def test_can_assign_editor_departments(self) -> None:
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        fp = FormPermissionsFactory(editor_departments=[eng, sales])
        self.assertEqual(fp.editor_departments.count(), 2)
        self.assertIn(eng, fp.editor_departments.all())
        self.assertIn(sales, fp.editor_departments.all())

    def test_can_assign_viewer_departments(self) -> None:
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(viewer_departments=[finance])
        self.assertEqual(fp.viewer_departments.count(), 1)
        self.assertIn(finance, fp.viewer_departments.all())

    def test_editor_and_viewer_departments_are_independent(self) -> None:
        it_dept = DepartmentFactory(name="IT")
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(
            editor_departments=[it_dept], viewer_departments=[finance]
        )
        self.assertIn(it_dept, fp.editor_departments.all())
        self.assertNotIn(it_dept, fp.viewer_departments.all())
        self.assertIn(finance, fp.viewer_departments.all())
        self.assertNotIn(finance, fp.editor_departments.all())

    def test_a_department_can_be_both_editor_and_viewer(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        fp = FormPermissionsFactory(
            editor_departments=[dept], viewer_departments=[dept]
        )
        self.assertIn(dept, fp.editor_departments.all())
        self.assertIn(dept, fp.viewer_departments.all())

    def test_can_assign_editor_users(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(editor_users=[alice, bob])
        self.assertEqual(fp.editor_users.count(), 2)
        self.assertIn(alice, fp.editor_users.all())
        self.assertIn(bob, fp.editor_users.all())

    def test_can_assign_viewer_users(self) -> None:
        carol = UserFactory()
        fp = FormPermissionsFactory(viewer_users=[carol])
        self.assertEqual(fp.viewer_users.count(), 1)
        self.assertIn(carol, fp.viewer_users.all())

    def test_editor_and_viewer_users_are_independent(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        fp = FormPermissionsFactory(editor_users=[alice], viewer_users=[bob])
        self.assertIn(alice, fp.editor_users.all())
        self.assertNotIn(alice, fp.viewer_users.all())
        self.assertIn(bob, fp.viewer_users.all())
        self.assertNotIn(bob, fp.editor_users.all())

    def test_a_user_can_be_both_editor_and_viewer(self) -> None:
        user = UserFactory()
        fp = FormPermissionsFactory(editor_users=[user], viewer_users=[user])
        self.assertIn(user, fp.editor_users.all())
        self.assertIn(user, fp.viewer_users.all())

    def test_a_form_can_only_have_one_form_permissions_row(self) -> None:
        fp = FormPermissionsFactory()
        with self.assertRaises(IntegrityError), transaction.atomic():
            FormPermissionsFactory(form=fp.form)
