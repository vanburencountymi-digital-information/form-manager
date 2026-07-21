from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions.context_processors import user_roles


class UserRolesIsDepartmentOwnerTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_false_for_user_with_no_owned_departments(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        self.assertFalse(user_roles(request)["is_a_department_owner"])

    def test_true_for_department_owner(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(request.user)
        self.assertTrue(user_roles(request)["is_a_department_owner"])

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(user_roles(request)["is_a_department_owner"])


class UserRolesIsAdministratorTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_false_for_non_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        self.assertFalse(user_roles(request)["is_administrator"])

    def test_true_for_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory(is_administrator=True)
        self.assertTrue(user_roles(request)["is_administrator"])

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(user_roles(request)["is_administrator"])


class UserRolesCanManageFormsTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_false_for_plain_user(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        self.assertFalse(user_roles(request)["can_manage_forms"])

    def test_true_for_department_owner(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(request.user)
        self.assertTrue(user_roles(request)["can_manage_forms"])

    def test_true_for_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory(is_administrator=True)
        self.assertTrue(user_roles(request)["can_manage_forms"])

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(user_roles(request)["can_manage_forms"])


class UserRolesCanManageDepartmentUsersTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_false_for_plain_user(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        self.assertFalse(user_roles(request)["can_manage_department_users"])

    def test_true_for_department_owner(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(request.user)
        self.assertTrue(user_roles(request)["can_manage_department_users"])

    def test_true_for_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory(is_administrator=True)
        self.assertTrue(user_roles(request)["can_manage_department_users"])

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertFalse(user_roles(request)["can_manage_department_users"])


class UserRolesShortCircuitsForUnauthenticatedTests(TestCase):
    """user_roles checks authentication once, up front, rather than relying
    on each individual check's own guard — see permissions/guards.py's
    is_authenticated_user."""

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_all_false_for_anonymous_user(self) -> None:
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertEqual(
            user_roles(request),
            {
                "is_a_department_owner": False,
                "is_administrator": False,
                "can_manage_forms": False,
                "can_manage_department_users": False,
            },
        )

    def test_all_false_when_request_has_no_user_attribute(self) -> None:
        request = self.factory.get("/")
        self.assertEqual(
            user_roles(request),
            {
                "is_a_department_owner": False,
                "is_administrator": False,
                "can_manage_forms": False,
                "can_manage_department_users": False,
            },
        )
