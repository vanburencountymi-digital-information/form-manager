from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions import checks


class IsDepartmentOwnerTests(TestCase):
    def test_false_for_user_with_no_owned_departments(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.is_a_department_owner(user))

    def test_true_for_department_owner(self) -> None:
        user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(user)
        self.assertTrue(checks.is_a_department_owner(user))

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        # AnonymousUser is not None and has no owned_departments accessor
        # — this must not raise AttributeError.
        self.assertFalse(checks.is_a_department_owner(AnonymousUser()))

    def test_false_for_none(self) -> None:
        self.assertFalse(checks.is_a_department_owner(None))


class IsAdministratorTests(TestCase):
    def test_false_for_non_administrator(self) -> None:
        user = UserFactory()
        self.assertFalse(checks.is_administrator(user))

    def test_true_for_administrator(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(checks.is_administrator(user))

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        self.assertFalse(checks.is_administrator(AnonymousUser()))

    def test_false_for_none(self) -> None:
        self.assertFalse(checks.is_administrator(None))


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

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        self.assertFalse(checks.can_create_forms(AnonymousUser()))

    def test_false_for_none(self) -> None:
        self.assertFalse(checks.can_create_forms(None))


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

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        self.assertFalse(checks.can_edit_forms(AnonymousUser()))

    def test_false_for_none(self) -> None:
        self.assertFalse(checks.can_edit_forms(None))
