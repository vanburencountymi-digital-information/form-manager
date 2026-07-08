from django.test import SimpleTestCase, override_settings

from accounts.forms import InviteUserForm

@override_settings(USER_EMAIL_DOMAINS=["example.com", "foo.com"])
class InviteUserFormTests(SimpleTestCase):

    def _assemble_form(self, email: str = ""):
        data = {
            "email": email,
            "first_name": "Jane",
            "last_name": "Doe",
        }
        return InviteUserForm(data=data)

    def test_valid_when_domain_is_allowlisted(self):
        form = self._assemble_form(email="jane@example.com")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "jane@example.com")

    def test_invalid_when_domain_is_not_allowlisted(self):
        form = self._assemble_form(email="jane@not-allowed.com")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"], ["This email domain is not allowed."]
        )

    def test_domain_check_is_case_insensitive(self):
        form = self._assemble_form(email="Jane@EXAMPLE.COM")
        self.assertTrue(form.is_valid(), form.errors)

    def test_second_allowlisted_domain_is_accepted(self):
        form = self._assemble_form(email="jane@foo.com")
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_email_is_rejected(self):
        form = self._assemble_form(email="")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @override_settings(USER_EMAIL_DOMAINS=[])
    def test_empty_allowlist_rejects_every_domain(self):
        form = self._assemble_form(email="jane@example.com")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
