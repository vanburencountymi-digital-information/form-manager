from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

User = get_user_model()


class UserSaveTests(TestCase):
    def test_save_lowercases_mixed_case_email(self):
        user = User.objects.create_user(username="jane", email="Jane@Example.com")
        self.assertEqual(user.email, "jane@example.com")

    def test_lowercasing_on_save_closes_case_variant_uniqueness_gap(self):
        User.objects.create_user(username="jane", email="Jane@Example.com")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(username="jane2", email="jane@example.com")
