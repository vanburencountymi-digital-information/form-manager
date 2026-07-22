import json

from django.test import TestCase
from django.urls import reverse

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.tests.factories import DepartmentUserFactory
from permissions.tests.factories import FormPermissionsFactory


class FormBuilderEditViewTests(TestCase):
    def setUp(self) -> None:
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=self.form_def, editor_departments=[self.department])
        self.url = reverse("form_builder_edit", kwargs={"form_id": self.form_def.id})

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_unrelated_user_is_denied(self) -> None:
        stranger = UserFactory()
        self.client.force_login(stranger)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_editor_department_owner_can_access_the_page(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_direct_editor_user_can_access_the_page(self) -> None:
        editor = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_users=[editor])
        self.client.force_login(editor)
        response = self.client.get(
            reverse("form_builder_edit", kwargs={"form_id": form_def.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_administrator_can_access_any_form(self) -> None:
        admin = UserFactory(is_administrator=True)
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_missing_form_returns_404(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("form_builder_edit", kwargs={"form_id": 999999})
        )
        self.assertEqual(response.status_code, 404)

    def test_renders_the_non_admin_adapted_template(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        content = response.content.decode()
        self.assertNotIn("admin:", content)
        self.assertIn(self.form_def.name, content)


class FormBuilderApiLoadViewTests(TestCase):
    def setUp(self) -> None:
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory(name="Travel Request")
        FormPermissionsFactory(form=self.form_def, editor_departments=[self.department])
        self.url = reverse(
            "form_builder_api_load", kwargs={"form_id": self.form_def.id}
        )

    def test_unrelated_user_is_denied(self) -> None:
        stranger = UserFactory()
        self.client.force_login(stranger)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_editor_gets_the_forms_data(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Travel Request")
        self.assertEqual(data["id"], self.form_def.id)


class FormBuilderApiSaveViewTests(TestCase):
    def setUp(self) -> None:
        self.owner = UserFactory()
        self.department = DepartmentUserFactory(
            name="Engineering", with_owner=self.owner
        )
        self.form_def = FormDefinitionFactory(
            name="Original Name", slug="original-slug"
        )
        FormPermissionsFactory(form=self.form_def, editor_departments=[self.department])
        self.url = reverse("form_builder_api_save")

    def _post(self, payload, user=None):
        if user:
            self.client.force_login(user)
        return self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )

    def _payload(self, **overrides):
        data = {
            "id": self.form_def.id,
            "name": "Updated Name",
            "slug": self.form_def.slug,
            "fields": [],
        }
        data.update(overrides)
        return data

    def test_saves_and_updates_the_form(self) -> None:
        response = self._post(self._payload(), user=self.owner)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.form_def.refresh_from_db()
        self.assertEqual(self.form_def.name, "Updated Name")

    def test_unrelated_user_is_denied(self) -> None:
        stranger = UserFactory()
        response = self._post(self._payload(), user=stranger)
        self.assertEqual(response.status_code, 403)
        self.form_def.refresh_from_db()
        self.assertEqual(self.form_def.name, "Original Name")

    def test_missing_name_is_rejected(self) -> None:
        response = self._post(self._payload(name=""), user=self.owner)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_missing_slug_is_rejected(self) -> None:
        response = self._post(self._payload(slug=""), user=self.owner)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_missing_id_is_rejected(self) -> None:
        response = self._post(self._payload(id=None), user=self.owner)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_invalid_json_is_rejected(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url, data="not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.post(
            self.url,
            data=json.dumps(self._payload()),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_get_is_not_allowed(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class FormBuilderGlobalApiViewTests(TestCase):
    """The endpoints with no specific form in play — templates gallery and
    shared option lists — gated existentially via can_manage_forms."""

    def test_templates_denies_a_plain_user(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse("form_builder_api_templates"))
        self.assertEqual(response.status_code, 403)

    def test_templates_allows_a_department_owner(self) -> None:
        owner = UserFactory()
        DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.client.force_login(owner)
        response = self.client.get(reverse("form_builder_api_templates"))
        self.assertEqual(response.status_code, 200)

    def test_shared_lists_denies_a_plain_user(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse("form_builder_api_shared_lists"))
        self.assertEqual(response.status_code, 403)

    def test_shared_lists_allows_a_department_owner(self) -> None:
        owner = UserFactory()
        DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.client.force_login(owner)
        response = self.client.get(reverse("form_builder_api_shared_lists"))
        self.assertEqual(response.status_code, 200)

    def test_preview_denies_a_plain_user(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.post(
            reverse("form_builder_api_preview"),
            data=json.dumps({"fields": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_preview_allows_a_department_owner(self) -> None:
        owner = UserFactory()
        DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.client.force_login(owner)
        response = self.client.post(
            reverse("form_builder_api_preview"),
            data=json.dumps({"fields": []}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
