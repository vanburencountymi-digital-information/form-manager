from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory
from permissions import checks
from permissions.guards import UnauthenticatedUserError


class IsDepartmentOwnerTests(TestCase):
    def test_false_for_user_with_no_owned_departments(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.is_a_department_owner(user))

    def test_true_for_department_owner(self) -> None:
        user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(user)
        self.assertTrue(checks.is_a_department_owner(user))

    def test_raises_for_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.is_a_department_owner(AnonymousUser())

    def test_raises_for_none(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.is_a_department_owner(None)


class IsAdministratorTests(TestCase):
    def test_false_for_non_administrator(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.is_administrator(user))

    def test_true_for_administrator(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(checks.is_administrator(user))

    def test_raises_for_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.is_administrator(AnonymousUser())

    def test_raises_for_none(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.is_administrator(None)


class CanCreateFormsTests(TestCase):
    def test_false_for_plain_user(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.can_create_forms(user))

    def test_true_for_department_owner(self) -> None:
        user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(user)
        self.assertTrue(checks.can_create_forms(user))

    def test_true_for_administrator_with_no_owned_departments(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(checks.can_create_forms(user))

    def test_true_for_explicit_department_level_grant_with_no_ownership(self) -> None:
        user = UserFactory()
        DepartmentUserFactory(
            name="Engineering",
            with_permissions=[(user, DepartmentPermission.CAN_CREATE_FORMS)],
        )
        self.assertTrue(checks.can_create_forms(user))

    def test_false_for_a_department_level_grant_of_a_different_codename(self) -> None:
        user = UserFactory()
        DepartmentUserFactory(
            name="Engineering",
            with_permissions=[(user, DepartmentPermission.CAN_EDIT_FORMS)],
        )
        self.assertFalse(checks.can_create_forms(user))

    def test_raises_for_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.can_create_forms(AnonymousUser())

    def test_raises_for_none(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.can_create_forms(None)


class CanEditFormsTests(TestCase):
    def test_false_for_plain_user(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.can_edit_forms(user))

    def test_true_for_department_owner(self) -> None:
        user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(user)
        self.assertTrue(checks.can_edit_forms(user))

    def test_true_for_administrator_with_no_owned_departments(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(checks.can_edit_forms(user))

    def test_raises_for_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.can_edit_forms(AnonymousUser())

    def test_raises_for_none(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            checks.can_edit_forms(None)
