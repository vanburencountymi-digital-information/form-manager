from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import PersonalGroup
from accounts.tests.factories import UserFactory

User = get_user_model()


class UserSaveTests(TestCase):
    def test_save_lowercases_mixed_case_email(self) -> None:
        user = User.objects.create_user(
            username="placeholder", email="Jane@Example.com"
        )
        self.assertEqual(user.email, "jane@example.com")
        self.assertEqual(user.username, "jane@example.com")

    def test_lowercasing_on_save_closes_case_variant_uniqueness_gap(self) -> None:
        User.objects.create_user(username="jane", email="Jane@Example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="jane2", email="jane@example.com")

    def test_email_at_150_characters_passes_full_clean(self) -> None:
        email = ("a" * 138) + "@example.com"  # exactly 150 characters
        self.assertEqual(len(email), 150)
        user = UserFactory.build(username=email, email=email)
        user.set_unusable_password()
        user.full_clean()

    def test_email_over_150_characters_fails_full_clean(self) -> None:
        email = ("a" * 139) + "@example.com"  # exactly 151 characters
        self.assertEqual(len(email), 151)
        user = UserFactory.build(username=email, email=email)
        user.set_unusable_password()
        with self.assertRaises(ValidationError) as ctx:
            user.full_clean()
        self.assertIn("email", ctx.exception.message_dict)


class PersonalGroupTests(TestCase):
    def test_user_factory_creates_a_personal_group(self) -> None:
        user = UserFactory()
        self.assertTrue(PersonalGroup.objects.filter(owner=user).exists())

    def test_personal_group_is_named_after_the_users_pk(self) -> None:
        user = UserFactory()
        self.assertEqual(user.personal_group.name, f"user-{user.pk}")

    def test_user_is_a_member_of_their_own_personal_group(self) -> None:
        user = UserFactory()
        self.assertIn(user.personal_group, user.groups.all())

    def test_a_user_cannot_have_a_second_personal_group(self) -> None:
        user = UserFactory()
        with self.assertRaises(IntegrityError), transaction.atomic():
            PersonalGroup.objects.create(owner=user)

    def test_a_personal_group_requires_an_owner(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            PersonalGroup.objects.create()
