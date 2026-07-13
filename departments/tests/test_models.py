from django.contrib.auth import get_user_model
from django.test import TestCase

from departments.models import Department

User = get_user_model()


class DepartmentTests(TestCase):
    def test_creating_root_department_auto_creates_a_group(self):
        dept = Department.add_root(name="Engineering")
        self.assertIsNotNone(dept.group_id)
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_each_department_gets_its_own_group(self):
        eng = Department.add_root(name="Engineering")
        sales = Department.add_root(name="Sales")
        self.assertNotEqual(eng.group_id, sales.group_id)

    def test_root_department_has_no_parent(self):
        dept = Department.add_root(name="Engineering")
        self.assertIsNone(dept.get_parent())

    def test_child_department_reports_its_parent(self):
        parent = Department.add_root(name="Engineering")
        child = parent.add_child(name="Backend")
        self.assertEqual(child.get_parent().pk, parent.pk)

    def test_ancestors_include_full_parent_chain_root_first(self):
        grandparent = Department.add_root(name="Company")
        parent = grandparent.add_child(name="Engineering")
        child = parent.add_child(name="Backend")
        ancestor_names = list(child.get_ancestors().values_list("name", flat=True))
        self.assertEqual(ancestor_names, ["Company", "Engineering"])

    def test_department_can_be_created_with_no_owners(self):
        dept = Department.add_root(name="Engineering")
        self.assertEqual(dept.owners.count(), 0)

    def test_department_can_have_multiple_owners(self):
        dept = Department.add_root(name="Engineering")
        alice = User.objects.create_user(username="alice", email="alice@example.com")
        bob = User.objects.create_user(username="bob", email="bob@example.com")
        dept.owners.add(alice, bob)
        self.assertEqual(dept.owners.count(), 2)
        self.assertIn(alice, dept.owners.all())
        self.assertIn(bob, dept.owners.all())

    def test_str_returns_name(self):
        dept = Department.add_root(name="Engineering")
        self.assertEqual(str(dept), "Engineering")
