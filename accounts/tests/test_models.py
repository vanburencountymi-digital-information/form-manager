from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

User = get_user_model()


class UserSaveTests(TestCase):
    def test_save_lowercases_mixed_case_email(self):
        user = User.objects.create_user(username="placeholder", email="Jane@Example.com")
        self.assertEqual(user.email, "jane@example.com")
        self.assertEqual(user.username, "jane@example.com")

    def test_lowercasing_on_save_closes_case_variant_uniqueness_gap(self):
        User.objects.create_user(username="jane", email="Jane@Example.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(username="jane2", email="jane@example.com")

    def test_email_at_150_characters_passes_full_clean(self):
        email = ("a" * 138) + "@example.com"  # exactly 150 characters
        self.assertEqual(len(email), 150)
        user = User(username=email, email=email)
        user.set_unusable_password()
        user.full_clean()

    def test_email_over_150_characters_fails_full_clean(self):
        email = ("a" * 139) + "@example.com"  # exactly 151 characters
        self.assertEqual(len(email), 151)
        user = User(username=email, email=email)
        user.set_unusable_password()
        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()
        self.assertIn("email", ctx.exception.message_dict)
