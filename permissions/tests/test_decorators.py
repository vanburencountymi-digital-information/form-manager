from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.test import RequestFactory, TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.tests.factories import DepartmentUserFactory
from permissions.decorators import (
    get_manageable_form_or_403,
    require_has_manage_forms_role_anywhere,
    require_manage_permission_for_form_def,
)
from permissions.guards import UnauthenticatedUserError
from permissions.tests.factories import FormPermissionsFactory


class GetManageableFormOr403Tests(TestCase):
    def setUp(self) -> None:
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=self.form_def, editor_departments=[self.department])

    def test_returns_the_form_def_for_an_authorized_user(self) -> None:
        result = get_manageable_form_or_403(self.owner, self.form_def.id)
        self.assertEqual(result, self.form_def)

    def test_raises_permission_denied_for_an_unrelated_user(self) -> None:
        stranger = UserFactory()
        with self.assertRaises(PermissionDenied):
            get_manageable_form_or_403(stranger, self.form_def.id)

    def test_raises_404_for_a_missing_form(self) -> None:
        with self.assertRaises(Http404):
            get_manageable_form_or_403(self.owner, 999999)


class RequireManagePermissionForFormDefTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=self.form_def, editor_departments=[self.department])

        @require_manage_permission_for_form_def
        def stub_view(request, form_id, *, extra=None):
            return HttpResponse(f"ok:{form_id}:{extra}")

        self.stub_view = stub_view

    def _request(self, user):
        request = self.factory.get("/irrelevant/")
        request.user = user
        return request

    def test_calls_through_for_an_authorized_user(self) -> None:
        response = self.stub_view(
            self._request(self.owner), form_id=self.form_def.id, extra="x"
        )
        self.assertEqual(response.content.decode(), f"ok:{self.form_def.id}:x")

    def test_raises_permission_denied_for_an_unrelated_user(self) -> None:
        stranger = UserFactory()
        with self.assertRaises(PermissionDenied):
            self.stub_view(self._request(stranger), form_id=self.form_def.id)

    def test_raises_404_for_a_missing_form(self) -> None:
        with self.assertRaises(Http404):
            self.stub_view(self._request(self.owner), form_id=999999)

    def test_raises_for_an_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            self.stub_view(self._request(AnonymousUser()), form_id=self.form_def.id)


class RequireHasManageFormsRoleAnywhereTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

        @require_has_manage_forms_role_anywhere
        def stub_view(request, *, extra=None):
            return HttpResponse(f"ok:{extra}")

        self.stub_view = stub_view

    def _request(self, user):
        request = self.factory.get("/irrelevant/")
        request.user = user
        return request

    def test_calls_through_for_a_department_owner(self) -> None:
        owner = UserFactory()
        DepartmentUserFactory(name="Engineering", with_owner=owner)
        response = self.stub_view(self._request(owner), extra="x")
        self.assertEqual(response.content.decode(), "ok:x")

    def test_raises_permission_denied_for_a_plain_user(self) -> None:
        user = UserFactory()
        with self.assertRaises(PermissionDenied):
            self.stub_view(self._request(user))

    def test_raises_for_an_anonymous_user(self) -> None:
        with self.assertRaises(UnauthenticatedUserError):
            self.stub_view(self._request(AnonymousUser()))
