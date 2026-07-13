from django.test import TestCase

from accounts.factories import UserFactory
from departments.factories import DepartmentFactory
from departments.models import Department, DepartmentHasChildrenError


class DepartmentTests(TestCase):
    def test_creating_root_department_auto_creates_a_group(self):
        dept = DepartmentFactory(name="Engineering")
        self.assertIsNotNone(dept.group_id)
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_each_department_gets_its_own_group(self):
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        self.assertNotEqual(eng.group_id, sales.group_id)

    def test_root_department_has_no_parent(self):
        dept = DepartmentFactory(name="Engineering")
        self.assertIsNone(dept.get_parent())

    def test_child_department_reports_its_parent(self):
        parent = DepartmentFactory(name="Engineering")
        child = DepartmentFactory(name="Backend", parent=parent)
        self.assertEqual(child.get_parent().pk, parent.pk)

    def test_ancestors_include_full_parent_chain_root_first(self):
        # Named explicitly rather than via chain_depth, since this test
        # asserts on the specific identity/order of each level, not just
        # that N levels exist.
        grandparent = DepartmentFactory(name="Company")
        parent = DepartmentFactory(name="Engineering", parent=grandparent)
        child = DepartmentFactory(name="Backend", parent=parent)
        ancestor_names = list(child.get_ancestors().values_list("name", flat=True))
        self.assertEqual(ancestor_names, ["Company", "Engineering"])

    def test_department_can_be_created_with_no_owners(self):
        dept = DepartmentFactory(name="Engineering")
        self.assertEqual(dept.owners.count(), 0)

    def test_department_can_have_multiple_owners(self):
        alice = UserFactory(email="alice@example.com")
        bob = UserFactory(email="bob@example.com")
        dept = DepartmentFactory(name="Engineering", owners=[alice, bob])
        self.assertEqual(dept.owners.count(), 2)
        self.assertIn(alice, dept.owners.all())
        self.assertIn(bob, dept.owners.all())

    def test_str_returns_name(self):
        dept = DepartmentFactory(name="Engineering")
        self.assertEqual(str(dept), "Engineering")

    def test_archive_marks_department_as_archived(self):
        dept = DepartmentFactory(name="Engineering")
        dept.archive()
        dept.refresh_from_db()
        self.assertTrue(dept.is_archived)

    def test_archive_raises_if_department_has_children(self):
        parent = DepartmentFactory(name="Engineering", chain_depth=1)
        with self.assertRaises(DepartmentHasChildrenError):
            parent.archive()
        parent.refresh_from_db()
        self.assertFalse(parent.is_archived)

    def test_archive_succeeds_after_children_are_moved_out(self):
        parent = DepartmentFactory(name="Engineering")
        other_root = DepartmentFactory(name="Sales")
        child = DepartmentFactory(name="Backend", parent=parent)
        child.move(other_root, pos="last-child")
        parent.archive()
        parent.refresh_from_db()
        self.assertTrue(parent.is_archived)

    def test_instance_delete_is_blocked(self):
        dept = DepartmentFactory(name="Engineering")
        with self.assertRaises(PermissionError):
            dept.delete()

    def test_queryset_bulk_delete_is_also_blocked(self):
        dept = DepartmentFactory(name="Engineering")
        with self.assertRaises(PermissionError):
            Department.objects.filter(pk=dept.pk).delete()
