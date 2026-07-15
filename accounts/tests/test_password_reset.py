from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tests.factories import UserFactory


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetPagesTests(TestCase):
    """Tests that don't need an existing user."""

    def test_reset_form_page_renders(self) -> None:
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)

    def test_submitting_an_unknown_email_does_not_send_an_email(self) -> None:
        self.client.post(reverse("password_reset"), {"email": "nobody@example.com"})
        self.assertEqual(len(mail.outbox), 0)

    def test_submitting_redirects_to_the_done_page(self) -> None:
        """Asserts view doesn't leak whether user does or doesn't exist"""
        response = self.client.post(
            reverse("password_reset"), {"email": "nobody@example.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))

    def test_complete_page_renders(self) -> None:
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetFlowTests(TestCase):
    """Tests that exercise the flow against a real user."""

    def setUp(self) -> None:
        self.user = UserFactory(email="jane@example.com", password="oldpass123")

    def _confirm_url(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})

    def test_submitting_a_known_email_sends_a_reset_email(self) -> None:
        self.client.post(reverse("password_reset"), {"email": "jane@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("jane@example.com", mail.outbox[0].body)

    def test_unusable_password_user_still_gets_a_reset_email(self) -> None:
        # Invited users start out with an unusable password (see
        # InviteUserForm) — reset doubles as account activation for them,
        # so the default has_usable_password() exclusion doesn't apply.
        self.user.set_unusable_password()
        self.user.save()
        self.client.post(reverse("password_reset"), {"email": "jane@example.com"})
        self.assertEqual(len(mail.outbox), 1)

    def test_valid_link_allows_setting_a_new_password(self) -> None:
        # The confirm view redirects the token out of the URL and into the
        # session on first GET, per Django's built-in flow.
        response = self.client.get(self._confirm_url(), follow=True)
        set_password_url = response.redirect_chain[-1][0]

        response = self.client.post(
            set_password_url,
            {"new_password1": "newpass456!", "new_password2": "newpass456!"},
        )
        self.assertRedirects(response, reverse("password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass456!"))

    def test_invalid_token_does_not_allow_setting_a_new_password(self) -> None:
        bad_url = reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(self.user.pk)),
                "token": "not-a-real-token",
            },
        )
        response = self.client.get(bad_url, follow=True)
        self.assertContains(response, "invalid", status_code=200)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("oldpass123"))
