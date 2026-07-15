from django.test import TestCase
from django.urls import reverse

from accounts.tests.factories import UserFactory


class LandingInternalViewTests(TestCase):
    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_user_sees_the_landing_page(self) -> None:
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_to_landing_page_by_default(self) -> None:
        user = UserFactory(password="pw12345!")
        response = self.client.post(
            reverse("login"), {"username": user.email, "password": "pw12345!"}
        )
        self.assertRedirects(response, "/")
