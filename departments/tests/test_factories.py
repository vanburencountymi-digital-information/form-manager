from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentUserFactory


class DepartmentUserFactoryOwnersTests(TestCase):
    def test_each_passed_in_user_becomes_an_owner(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        dept = DepartmentUserFactory(owners=[alice, bob])
        self.assertIn(alice, dept.owners.all())
        self.assertIn(bob, dept.owners.all())

    def test_each_passed_in_user_also_becomes_a_member(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        dept = DepartmentUserFactory(owners=[alice, bob])
        self.assertIn(dept.group, alice.groups.all())
        self.assertIn(dept.group, bob.groups.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentUserFactory()
        self.assertEqual(dept.owners.count(), 0)


class DepartmentUserFactoryWithOwnerTests(TestCase):
    def test_true_auto_generates_an_owner(self) -> None:
        dept = DepartmentUserFactory(with_owner=True)
        self.assertEqual(dept.owners.count(), 1)

    def test_true_also_adds_the_owner_as_a_member(self) -> None:
        dept = DepartmentUserFactory(with_owner=True)
        owner = dept.owners.get()
        self.assertIn(dept.group, owner.groups.all())

    def test_specific_user_is_used_as_the_owner(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_owner=user)
        self.assertIn(user, dept.owners.all())

    def test_specific_user_is_also_added_as_a_member(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_owner=user)
        self.assertIn(dept.group, user.groups.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentUserFactory()
        self.assertEqual(dept.owners.count(), 0)


class DepartmentUserFactoryWithUserTests(TestCase):
    def test_true_auto_generates_a_member(self) -> None:
        dept = DepartmentUserFactory(with_user=True)
        self.assertEqual(dept.group.user_set.count(), 1)

    def test_true_does_not_make_the_member_an_owner(self) -> None:
        dept = DepartmentUserFactory(with_user=True)
        member = dept.group.user_set.get()
        self.assertNotIn(member, dept.owners.all())

    def test_specific_user_is_used_as_the_member(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_user=user)
        self.assertIn(dept.group, user.groups.all())

    def test_specific_user_is_not_added_as_an_owner(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_user=user)
        self.assertNotIn(user, dept.owners.all())

    def test_omitted_by_default(self) -> None:
        dept = DepartmentUserFactory()
        self.assertEqual(dept.group.user_set.count(), 0)


class DepartmentUserFactoryWithPermissionsTests(TestCase):
    def test_grants_the_given_permission_to_the_given_user(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)]
        )
        self.assertTrue(
            user.has_perm(f"departments.{DepartmentPermission.CAN_MANAGE_FORMS}", dept)
        )

    def test_does_not_grant_a_permission_not_listed(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)]
        )
        self.assertFalse(
            user.has_perm(
                f"departments.{DepartmentPermission.CAN_MANAGE_WORKFLOWS}", dept
            )
        )

    def test_does_not_grant_it_to_an_unrelated_user(self) -> None:
        user = UserFactory()
        other_user = UserFactory()
        dept = DepartmentUserFactory(
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)]
        )
        self.assertFalse(
            other_user.has_perm(
                f"departments.{DepartmentPermission.CAN_MANAGE_FORMS}", dept
            )
        )

    def test_does_not_imply_membership(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)]
        )
        self.assertNotIn(dept.group, user.groups.all())

    def test_multiple_pairs_are_all_applied(self) -> None:
        alice = UserFactory()
        bob = UserFactory()
        dept = DepartmentUserFactory(
            with_permissions=[
                (alice, DepartmentPermission.CAN_MANAGE_FORMS),
                (bob, DepartmentPermission.CAN_MANAGE_WORKFLOWS),
            ]
        )
        self.assertTrue(
            alice.has_perm(f"departments.{DepartmentPermission.CAN_MANAGE_FORMS}", dept)
        )
        self.assertTrue(
            bob.has_perm(
                f"departments.{DepartmentPermission.CAN_MANAGE_WORKFLOWS}", dept
            )
        )

    def test_omitted_by_default(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory()
        self.assertFalse(
            user.has_perm(f"departments.{DepartmentPermission.CAN_MANAGE_FORMS}", dept)
        )
