from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory


class DepartmentFactoryOwnersTests(TestCase):
    def test_each_passed_in_user_becomes_an_owner(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        dept = DepartmentFactory(owners=[alice, bob])
        self.assertIn(alice, dept.owners.all())
        self.assertIn(bob, dept.owners.all())

    def test_each_passed_in_user_also_becomes_a_member(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        dept = DepartmentFactory(owners=[alice, bob])
        self.assertIn(dept.group, alice.groups.all())
        self.assertIn(dept.group, bob.groups.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentFactory()
        self.assertEqual(dept.owners.count(), 0)


class DepartmentFactoryWithOwnerTests(TestCase):
    def test_true_auto_generates_an_owner(self) -> None:
        dept = DepartmentFactory(with_owner=True)
        self.assertEqual(dept.owners.count(), 1)

    def test_true_also_adds_the_owner_as_a_member(self) -> None:
        dept = DepartmentFactory(with_owner=True)
        owner = dept.owners.get()
        self.assertIn(dept.group, owner.groups.all())

    def test_specific_user_is_used_as_the_owner(self) -> None:
        user = UserFactory()
        dept = DepartmentFactory(with_owner=user)
        self.assertIn(user, dept.owners.all())

    def test_specific_user_is_also_added_as_a_member(self) -> None:
        user = UserFactory()
        dept = DepartmentFactory(with_owner=user)
        self.assertIn(dept.group, user.groups.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentFactory()
        self.assertEqual(dept.owners.count(), 0)


class DepartmentFactoryWithUserTests(TestCase):
    def test_true_auto_generates_a_member(self) -> None:
        dept = DepartmentFactory(with_user=True)
        self.assertEqual(dept.group.user_set.count(), 1)

    def test_true_does_not_make_the_member_an_owner(self) -> None:
        dept = DepartmentFactory(with_user=True)
        member = dept.group.user_set.get()
        self.assertNotIn(member, dept.owners.all())

    def test_specific_user_is_used_as_the_member(self) -> None:
        user = UserFactory()
        dept = DepartmentFactory(with_user=user)
        self.assertIn(dept.group, user.groups.all())

    def test_specific_user_is_not_added_as_an_owner(self) -> None:
        user = UserFactory()
        dept = DepartmentFactory(with_user=user)
        self.assertNotIn(user, dept.owners.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentFactory()
        self.assertEqual(dept.group.user_set.count(), 0)
