from typing import Any

from django.test import TestCase

from accounts.models import PersonalGroup
from accounts.services.user_service import UserService
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentFactory
from permissions.services.admin_group_service import AdministratorGroupService
from permissions.services.department_perm_service import DepartmentPermissionsService


class UserServiceCreateUserTests(TestCase):
    def setUp(self) -> None:
        self.department = DepartmentFactory(name="Engineering")

    def _create(self, **overrides: Any):
        kwargs: dict[str, Any] = {
            "email": "jane@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "department": self.department,
        }
        kwargs.update(overrides)
        return UserService.create_user(**kwargs)

    def test_creates_a_user_with_an_unusable_password(self) -> None:
        user = self._create()
        self.assertFalse(user.has_usable_password())

    def test_creates_a_personal_group_and_adds_membership(self) -> None:
        user = self._create()
        self.assertTrue(PersonalGroup.objects.filter(owner=user).exists())
        self.assertIn(user.personal_group, user.groups.all())

    def test_adds_user_to_department(self) -> None:
        user = self._create()
        self.assertTrue(self.department.check_if_user_is_member(user))

    def test_does_not_grant_ownership_by_default(self) -> None:
        user = self._create()
        self.assertFalse(self.department.check_if_owned_by_user(user))

    def test_is_department_owner_grants_ownership(self) -> None:
        user = self._create(is_department_owner=True)
        self.assertTrue(self.department.check_if_owned_by_user(user))

    def test_can_create_forms_grants_the_department_permission(self) -> None:
        user = self._create(can_create_forms=True)
        self.assertTrue(
            DepartmentPermissionsService.has_permission(
                user, self.department, DepartmentPermission.CAN_CREATE_FORMS
            )
        )

    def test_can_create_forms_false_by_default(self) -> None:
        user = self._create()
        self.assertFalse(
            DepartmentPermissionsService.has_permission(
                user, self.department, DepartmentPermission.CAN_CREATE_FORMS
            )
        )

    def test_is_administrator_grants_administrator(self) -> None:
        user = self._create(is_administrator=True)
        self.assertTrue(AdministratorGroupService.is_administrator(user))

    def test_is_administrator_false_by_default(self) -> None:
        user = self._create()
        self.assertFalse(AdministratorGroupService.is_administrator(user))
