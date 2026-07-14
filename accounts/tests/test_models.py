from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.tests.factories import UserFactory

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


class GetOrCreatePersonalGroupTests(TestCase):
    def test_no_personal_group_exists_before_it_is_called(self):
        user = UserFactory()
        self.assertFalse(Group.objects.filter(name=f"user-{user.pk}").exists())

    def test_creates_a_group_named_after_the_users_pk(self):
        user = UserFactory()
        group = user.get_or_create_personal_group()
        self.assertEqual(group.name, f"user-{user.pk}")

    def test_adds_the_user_to_the_group(self):
        user = UserFactory()
        group = user.get_or_create_personal_group()
        self.assertIn(group, user.groups.all())

    def test_calling_it_again_returns_the_same_group(self):
        user = UserFactory()
        first = user.get_or_create_personal_group()
        second = user.get_or_create_personal_group()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Group.objects.filter(name=f"user-{user.pk}").count(), 1)
