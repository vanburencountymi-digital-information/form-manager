import itertools

from django.test import TestCase
from parameterized import parameterized

from accounts.tests.factories import UserFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory
from permissions.services.department_perm_service import DepartmentPermissionsService


class DepartmentPermissionsServiceHasPermissionTests(TestCase):
    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_true_for_department_owner_with_no_explicit_grant(
        self, codename: DepartmentPermission
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        user = UserFactory()
        dept.add_user_to_owners(user)
        self.assertTrue(
            DepartmentPermissionsService.has_permission(user, dept, codename)
        )

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_true_for_user_with_explicit_guardian_grant(
        self, codename: DepartmentPermission
    ) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering", with_permissions=[(user, codename)]
        )
        self.assertTrue(
            DepartmentPermissionsService.has_permission(user, dept, codename)
        )

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_false_for_plain_member_with_no_grant(
        self, codename: DepartmentPermission
    ) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        self.assertFalse(
            DepartmentPermissionsService.has_permission(user, dept, codename)
        )

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_false_for_owner_of_a_different_department(
        self, codename: DepartmentPermission
    ) -> None:
        dept = DepartmentFactory(name="Engineering")
        other_dept = DepartmentFactory(name="Sales")
        user = UserFactory()
        other_dept.add_user_to_owners(user)
        self.assertFalse(
            DepartmentPermissionsService.has_permission(user, dept, codename)
        )

    @parameterized.expand(list(itertools.permutations(DepartmentPermission, 2)))
    def test_grant_on_one_codename_does_not_imply_another(
        self, granted: DepartmentPermission, checked: DepartmentPermission
    ) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering", with_permissions=[(user, granted)]
        )
        self.assertFalse(
            DepartmentPermissionsService.has_permission(user, dept, checked)
        )


class DepartmentPermissionsServiceHasPermissionAnywhereTests(TestCase):
    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_true_for_a_grant_on_one_of_several_departments(
        self, codename: DepartmentPermission
    ) -> None:
        user = UserFactory()
        DepartmentFactory(name="Sales")
        DepartmentUserFactory(name="Engineering", with_permissions=[(user, codename)])
        self.assertTrue(
            DepartmentPermissionsService.has_permission_anywhere(user, codename)
        )

    @parameterized.expand([(codename,) for codename in DepartmentPermission])
    def test_false_with_no_grant_anywhere(self, codename: DepartmentPermission) -> None:
        user = UserFactory()
        DepartmentFactory(name="Engineering")
        self.assertFalse(
            DepartmentPermissionsService.has_permission_anywhere(user, codename)
        )

    def test_ownership_alone_does_not_count(self) -> None:
        # has_permission_anywhere only checks explicit guardian grants —
        # ownership is a separate axis, checked elsewhere (e.g.
        # checks.is_a_department_owner).
        owner = UserFactory()
        DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.assertFalse(
            DepartmentPermissionsService.has_permission_anywhere(
                owner, DepartmentPermission.CAN_CREATE_FORMS
            )
        )

    @parameterized.expand(list(itertools.permutations(DepartmentPermission, 2)))
    def test_grant_on_one_codename_does_not_imply_another(
        self, granted: DepartmentPermission, checked: DepartmentPermission
    ) -> None:
        user = UserFactory()
        DepartmentUserFactory(name="Engineering", with_permissions=[(user, granted)])
        self.assertFalse(
            DepartmentPermissionsService.has_permission_anywhere(user, checked)
        )
