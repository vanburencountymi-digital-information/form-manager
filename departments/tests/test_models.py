from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.shortcuts import assign_perm
from parameterized import parameterized

from accounts.tests.factories import UserFactory
from departments.models import (
    Department,
    DepartmentHasChildrenError,
    DepartmentPermission,
)
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory


class DepartmentTests(TestCase):
    def test_creating_root_department_auto_creates_a_group(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertIsNotNone(dept.group_id)
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_each_department_gets_its_own_group(self) -> None:
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        self.assertNotEqual(eng.group_id, sales.group_id)

    def test_group_name_property_reflects_current_name(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertEqual(dept.group_name, "dept-Engineering")
        dept.name = "Platform Engineering"
        self.assertEqual(dept.group_name, "dept-Platform Engineering")

    def test_sync_group_name_corrects_a_drifted_group_name(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        dept.group.name = "some-other-name"
        dept.group.save()
        dept.sync_group_name()
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_sync_group_name_is_a_noop_when_already_correct(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        dept.sync_group_name()
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_sync_group_name_creates_a_group_if_none_exists(self) -> None:
        dept = Department(name="Engineering")
        self.assertIsNone(dept.group_id)
        dept.sync_group_name()
        self.assertIsNotNone(dept.group_id)
        self.assertEqual(dept.group.name, "dept-Engineering")

    def test_renaming_a_department_and_saving_syncs_its_group_name(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        dept.name = "Platform Engineering"
        dept.save()
        dept.refresh_from_db()
        self.assertEqual(dept.group.name, "dept-Platform Engineering")

    def test_root_department_has_no_parent(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertIsNone(dept.get_parent())

    def test_child_department_reports_its_parent(self) -> None:
        parent = DepartmentFactory(name="Engineering")
        child = DepartmentFactory(name="Backend", parent=parent)
        self.assertEqual(child.get_parent().pk, parent.pk)

    def test_ancestors_include_full_parent_chain_root_first(self) -> None:
        # Named explicitly rather than via chain_depth, since this test
        # asserts on the specific identity/order of each level, not just
        # that N levels exist.
        grandparent = DepartmentFactory(name="Company")
        parent = DepartmentFactory(name="Engineering", parent=grandparent)
        child = DepartmentFactory(name="Backend", parent=parent)
        ancestor_names = list(child.get_ancestors().values_list("name", flat=True))
        self.assertEqual(ancestor_names, ["Company", "Engineering"])

    def test_department_can_be_created_with_no_owners(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertEqual(dept.owners.count(), 0)

    def test_department_can_have_multiple_owners(self) -> None:
        alice = UserFactory(email="alice@example.com")
        bob = UserFactory(email="bob@example.com")
        dept = DepartmentUserFactory(name="Engineering", owners=[alice, bob])
        self.assertEqual(dept.owners.count(), 2)
        self.assertIn(alice, dept.owners.all())
        self.assertIn(bob, dept.owners.all())
        self.assertIn(dept.group, alice.groups.all())
        self.assertIn(dept.group, bob.groups.all())

    def test_str_returns_name(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertEqual(str(dept), "Engineering")

    def test_add_member_adds_user_to_the_departments_group(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        self.assertIn(dept.group, user.groups.all())

    def test_remove_member_removes_user_from_the_departments_group(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        dept.remove_member(user)
        self.assertNotIn(dept.group, user.groups.all())

    def test_remove_member_also_removes_ownership(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        dept.add_user_to_owners(user)
        dept.remove_member(user)
        self.assertFalse(dept.check_if_owned_by_user(user))

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_remove_member_revokes_department_permissions_on_this_department(
        self, codename: DepartmentPermission
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        assign_perm(codename, user, dept)
        dept.remove_member(user)
        self.assertFalse(user.has_perm(f"departments.{codename}", dept))

    def test_remove_member_does_not_revoke_permissions_on_a_different_department(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        other_dept = DepartmentFactory(name="Sales")
        user = UserFactory()
        dept.add_member(user)
        other_dept.add_member(user)
        assign_perm(DepartmentPermission.CAN_CREATE_FORMS, user, other_dept)
        dept.remove_member(user)
        self.assertTrue(
            user.has_perm(
                f"departments.{DepartmentPermission.CAN_CREATE_FORMS}", other_dept
            )
        )

    def test_add_user_to_owners_adds_user_to_the_departments_owners(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        self.assertIn(user, dept.owners.all())

    def test_remove_user_from_owners_removes_user_from_the_departments_owners(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        dept.remove_user_from_owners(user)
        self.assertNotIn(user, dept.owners.all())

    def test_add_user_to_owners_does_not_also_add_membership(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        self.assertNotIn(dept.group, user.groups.all())

    def test_remove_user_from_owners_does_not_affect_membership(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        dept.add_user_to_owners(user)
        dept.remove_user_from_owners(user)
        self.assertIn(dept.group, user.groups.all())

    def test_check_if_owned_by_user_true_for_an_owner(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        self.assertTrue(dept.check_if_owned_by_user(user))

    def test_check_if_owned_by_user_false_for_a_non_owner(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        self.assertFalse(dept.check_if_owned_by_user(user))

    def test_check_if_owned_by_user_false_for_a_plain_member(self) -> None:
        # Membership alone (not ownership) shouldn't count.
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        self.assertFalse(dept.check_if_owned_by_user(user))

    def test_check_if_owned_by_user_false_for_owner_of_a_different_department(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        other_dept = DepartmentFactory(name="Sales")
        user = UserFactory()
        other_dept.add_user_to_owners(user)
        self.assertFalse(dept.check_if_owned_by_user(user))

    def test_check_if_user_is_member_true_for_a_member(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_member(user)
        self.assertTrue(dept.check_if_user_is_member(user))

    def test_check_if_user_is_member_false_for_a_non_member(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        self.assertFalse(dept.check_if_user_is_member(user))

    def test_check_if_user_is_member_false_for_an_owner_who_is_not_a_member(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        self.assertFalse(dept.check_if_user_is_member(user))

    def test_check_if_user_is_member_false_for_member_of_a_different_department(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        other_dept = DepartmentFactory(name="Sales")
        user = UserFactory()
        other_dept.add_member(user)
        self.assertFalse(dept.check_if_user_is_member(user))

    def test_check_if_owned_by_user_false_for_owner_of_a_descendant_department(
        self,
    ) -> None:
        # Unlike get_departments_owned_by_user, this checks direct ownership
        # of this exact department only — owning a child doesn't count.
        parent = DepartmentFactory(name="Engineering")
        child = DepartmentFactory(name="Backend", parent=parent)
        user = UserFactory()
        child.add_user_to_owners(user)
        self.assertFalse(parent.check_if_owned_by_user(user))

    def test_get_departments_owned_by_user_includes_directly_owned_departments(
        self,
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.owners.add(user)
        self.assertIn(dept, Department.get_departments_owned_by_user(user))

    def test_get_departments_owned_by_user_includes_descendants_of_owned_departments(
        self,
    ) -> None:
        parent = DepartmentFactory(name="Engineering")
        child = DepartmentFactory(name="Backend", parent=parent)
        grandchild = DepartmentFactory(name="Infra", parent=child)
        user = UserFactory()
        parent.owners.add(user)
        owned = Department.get_departments_owned_by_user(user)
        self.assertIn(child, owned)
        self.assertIn(grandchild, owned)

    def test_get_departments_owned_by_user_excludes_unrelated_departments(self) -> None:
        parent = DepartmentFactory(name="Engineering")
        unrelated = DepartmentFactory(name="Sales")
        user = UserFactory()
        parent.owners.add(user)
        self.assertNotIn(unrelated, Department.get_departments_owned_by_user(user))

    def test_archive_marks_department_as_archived(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        dept.archive()
        dept.refresh_from_db()
        self.assertTrue(dept.is_archived)

    def test_archive_raises_if_department_has_children(self) -> None:
        parent = DepartmentFactory(name="Engineering", chain_depth=1)
        with self.assertRaises(DepartmentHasChildrenError):
            parent.archive()
        parent.refresh_from_db()
        self.assertFalse(parent.is_archived)

    def test_archive_succeeds_after_children_are_moved_out(self) -> None:
        parent = DepartmentFactory(name="Engineering")
        other_root = DepartmentFactory(name="Sales")
        child = DepartmentFactory(name="Backend", parent=parent)
        child.move(other_root, pos="sorted-child")
        parent.archive()
        parent.refresh_from_db()
        self.assertTrue(parent.is_archived)

    def test_instance_delete_is_blocked(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        with self.assertRaises(PermissionError):
            dept.delete()

    def test_queryset_bulk_delete_is_also_blocked(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        with self.assertRaises(PermissionError):
            Department.objects.filter(pk=dept.pk).delete()


class DepartmentPermissionMetaTests(TestCase):
    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_codename_is_registered_as_a_permission(
        self, codename: DepartmentPermission
    ) -> None:
        content_type = ContentType.objects.get_for_model(Department)
        self.assertTrue(
            Permission.objects.filter(
                content_type=content_type, codename=codename.value
            ).exists()
        )

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_can_assign_and_check_an_object_level_department_permission(
        self, codename: DepartmentPermission
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        other_dept = DepartmentFactory(name="Sales")
        user = UserFactory()
        assign_perm(codename, user, dept)
        self.assertTrue(user.has_perm(f"departments.{codename}", dept))
        self.assertFalse(user.has_perm(f"departments.{codename}", other_dept))
