from unittest.mock import patch

from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from django_forms_workflows.models import FormDefinition

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.tests.factories import DepartmentUserFactory
from permissions.tests.factories import FormPermissionsFactory


class CreateFormPermissionsViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse("create_form_permissions")
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )

        # mock FormPermissionsService - this is tested separately in test_services
        service_patcher = patch("permissions.views.FormPermissionsService")
        self.mock_service = service_patcher.start()
        self.addCleanup(service_patcher.stop)

        redirect_patcher = patch("permissions.views.redirect")
        self.mock_redirect = redirect_patcher.start()
        self.mock_redirect.return_value = HttpResponse(status=302)
        self.addCleanup(redirect_patcher.stop)

    def _post_data(self, **overrides):
        data = {
            "name": "Travel Request",
            "requires_login": "on",
            "departments": [self.department.pk],
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_user_without_can_manage_forms_is_denied(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_department_owner_can_access_the_page(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_calls_create_form_permissions_with_the_right_arguments(self) -> None:
        editor = UserFactory()
        viewer = UserFactory()
        self.client.force_login(self.owner)
        self.client.post(
            self.url,
            self._post_data(
                editor_users=[editor.pk], submission_viewer_users=[viewer.pk]
            ),
        )
        form_def = FormDefinition.objects.get(name="Travel Request")
        self.mock_service.create_form_permissions.assert_called_once()
        _, kwargs = self.mock_service.create_form_permissions.call_args
        self.assertEqual(kwargs["form_def"], form_def)
        self.assertEqual(list(kwargs["editor_departments"]), [self.department])
        self.assertEqual(list(kwargs["editor_users"]), [editor])
        self.assertEqual(list(kwargs["submission_viewer_users"]), [viewer])

    def test_post_creates_the_form_definition(self) -> None:
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data())
        form_def = FormDefinition.objects.get(name="Travel Request")
        self.assertTrue(form_def.requires_login)

    def test_post_redirects_to_form_builder_edit_with_the_new_form_id(self) -> None:
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data())
        form_def = FormDefinition.objects.get(name="Travel Request")
        self.mock_redirect.assert_called_once_with(
            "form_builder_edit", form_id=form_def.id
        )

    def test_invalid_post_does_not_create_a_form_and_rerenders(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data(name=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FormDefinition.objects.filter(requires_login=True).exists())
        self.assertTrue(response.context["form"].errors)
        self.mock_service.create_form_permissions.assert_not_called()

    def test_post_with_no_department_is_rejected(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data(departments=[]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.mock_service.create_form_permissions.assert_not_called()


class EditFormPermissionsViewTests(TestCase):
    # Same mocking rationale as CreateFormPermissionsViewTests —
    # FormPermissionsService.update_form_permissions already has its own
    # dedicated tests against the real DB.

    def setUp(self) -> None:
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory()
        self.form_permissions = FormPermissionsFactory(
            form=self.form_def, editor_departments=[self.department]
        )
        self.url = reverse(
            "edit_form_permissions", kwargs={"form_id": self.form_def.id}
        )

        service_patcher = patch("permissions.views.FormPermissionsService")
        self.mock_service = service_patcher.start()
        self.addCleanup(service_patcher.stop)

    def _post_data(self, **overrides):
        data = {
            "editor_departments": [self.department.pk],
            "editor_users": [],
            "submission_viewer_users": [],
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_unrelated_user_is_denied(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_editor_department_owner_can_access_the_page(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_missing_form_returns_404(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("edit_form_permissions", kwargs={"form_id": 999999})
        )
        self.assertEqual(response.status_code, 404)

    def test_post_calls_update_form_permissions_with_the_right_arguments(self) -> None:
        other_department = DepartmentUserFactory(name="Sales", with_owner=self.owner)
        viewer = UserFactory()
        self.client.force_login(self.owner)
        self.client.post(
            self.url,
            self._post_data(
                editor_departments=[other_department.pk],
                submission_viewer_users=[viewer.pk],
            ),
        )
        self.mock_service.update_form_permissions.assert_called_once()
        args, kwargs = self.mock_service.update_form_permissions.call_args
        self.assertEqual(args[0], self.form_permissions)
        self.assertEqual(list(kwargs["editor_departments"]), [other_department])
        self.assertEqual(list(kwargs["editor_users"]), [])
        self.assertEqual(list(kwargs["submission_viewer_users"]), [viewer])

    def test_post_redirects_to_self(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(self.url, self._post_data())
        self.assertRedirects(response, self.url)

    def test_invalid_post_does_not_call_the_service(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url, self._post_data(editor_departments=["not-a-valid-pk"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.mock_service.update_form_permissions.assert_not_called()
