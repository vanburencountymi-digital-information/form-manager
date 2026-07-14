from django.db import IntegrityError, transaction
from django.test import TestCase

from departments.tests.factories import DepartmentFactory
from permissions.tests.factories import FormPermissionsFactory


class FormPermissionsTests(TestCase):
    def test_created_with_no_departments_by_default(self):
        fp = FormPermissionsFactory()
        self.assertEqual(fp.editor_departments.count(), 0)
        self.assertEqual(fp.viewer_departments.count(), 0)

    def test_can_assign_editor_departments(self):
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        fp = FormPermissionsFactory(editor_departments=[eng, sales])
        self.assertEqual(fp.editor_departments.count(), 2)
        self.assertIn(eng, fp.editor_departments.all())
        self.assertIn(sales, fp.editor_departments.all())

    def test_can_assign_viewer_departments(self):
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(viewer_departments=[finance])
        self.assertEqual(fp.viewer_departments.count(), 1)
        self.assertIn(finance, fp.viewer_departments.all())

    def test_editor_and_viewer_departments_are_independent(self):
        it_dept = DepartmentFactory(name="IT")
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(
            editor_departments=[it_dept], viewer_departments=[finance]
        )
        self.assertIn(it_dept, fp.editor_departments.all())
        self.assertNotIn(it_dept, fp.viewer_departments.all())
        self.assertIn(finance, fp.viewer_departments.all())
        self.assertNotIn(finance, fp.editor_departments.all())

    def test_a_department_can_be_both_editor_and_viewer(self):
        dept = DepartmentFactory(name="Engineering")
        fp = FormPermissionsFactory(editor_departments=[dept], viewer_departments=[dept])
        self.assertIn(dept, fp.editor_departments.all())
        self.assertIn(dept, fp.viewer_departments.all())

    def test_a_form_can_only_have_one_form_permissions_row(self):
        fp = FormPermissionsFactory()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormPermissionsFactory(form=fp.form)
