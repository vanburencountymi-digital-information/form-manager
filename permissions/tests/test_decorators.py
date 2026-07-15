from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions.decorators import admin_or_dept_owner_required, administrator_required


class AdministratorRequiredTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        @administrator_required
        def dummy_view(request):
            return "ok"

        self.dummy_view = dummy_view

    def test_denies_non_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        with self.assertRaises(PermissionDenied):
            self.dummy_view(request)

    def test_allows_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory(is_administrator=True)
        self.assertEqual(self.dummy_view(request), "ok")


class DepartmentManagerRequiredTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        @admin_or_dept_owner_required
        def dummy_view(request):
            return "ok"

        self.dummy_view = dummy_view

    def test_denies_user_with_no_departments_and_not_administrator(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        with self.assertRaises(PermissionDenied):
            self.dummy_view(request)

    def test_allows_department_owner(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory()
        DepartmentFactory(name="Engineering").owners.add(request.user)
        self.assertEqual(self.dummy_view(request), "ok")

    def test_allows_administrator_with_no_owned_departments(self) -> None:
        request = self.factory.get("/")
        request.user = UserFactory(is_administrator=True)
        self.assertEqual(self.dummy_view(request), "ok")
