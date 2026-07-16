from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions.services.admin_group_service import AdministratorGroupService

User = get_user_model()


@override_settings(USER_EMAIL_DOMAINS=["example.com"])
class InviteUserViewTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse("invite_user")
        self.department = DepartmentFactory(name="Engineering")
        self.owner = UserFactory()
        self.department.owners.add(self.owner)

    def _post_data(self, **overrides):
        data = {
            "email": "jane@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "department": self.department.pk,
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_user_with_no_department_and_not_administrator_is_denied(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_department_owner_can_access_the_page(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_administrator_with_no_owned_department_can_access_the_page(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        self.client.force_login(admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_owner_post_creates_user_and_adds_to_department(self) -> None:
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data())
        new_user = User.objects.get(email="jane@example.com")
        self.assertIn(self.department.group, new_user.groups.all())

    def test_invited_user_has_an_unusable_password(self) -> None:
        # Invited users have never set a password — the reset flow
        # doubles as account activation, but only if this is set
        # correctly (an empty password field would be falsely "usable").
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data())
        new_user = User.objects.get(email="jane@example.com")
        self.assertFalse(new_user.has_usable_password())

    def test_owner_post_with_no_department_creates_user_with_no_group(self) -> None:
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(department=""))
        new_user = User.objects.get(email="jane@example.com")
        self.assertEqual(new_user.groups.count(), 0)

    def test_invalid_post_does_not_create_a_user_and_re_renders(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(
            self.url, self._post_data(email="jane@not-allowed.com")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="jane@not-allowed.com").exists())
        self.assertTrue(response.context["form"].errors)

    def test_owner_cannot_grant_administrator_via_tampered_post(self) -> None:
        self.client.force_login(self.owner)
        self.client.post(self.url, self._post_data(is_administrator="on"))
        new_user = User.objects.get(email="jane@example.com")
        self.assertFalse(AdministratorGroupService.is_administrator(new_user))

    def test_administrator_post_without_flag_does_not_grant_administrator(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        self.department.owners.add(admin_user)
        self.client.force_login(admin_user)
        self.client.post(self.url, self._post_data())
        new_user = User.objects.get(email="jane@example.com")
        self.assertFalse(AdministratorGroupService.is_administrator(new_user))

    def test_administrator_post_with_flag_grants_administrator(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        self.department.owners.add(admin_user)
        self.client.force_login(admin_user)
        self.client.post(self.url, self._post_data(is_administrator="on"))
        new_user = User.objects.get(email="jane@example.com")
        self.assertTrue(AdministratorGroupService.is_administrator(new_user))
