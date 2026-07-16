from django.contrib.auth.models import Group
from django.test import TestCase

from accounts.tests.factories import UserFactory
from permissions.services.admin_group_service import AdministratorGroupService


class AdministratorGroupServiceGetOrCreateGroupTests(TestCase):
    def test_creates_group_if_missing(self) -> None:
        self.assertFalse(
            Group.objects.filter(name=AdministratorGroupService.GROUP_NAME).exists()
        )
        group = AdministratorGroupService.get_or_create_group()
        self.assertEqual(group.name, AdministratorGroupService.GROUP_NAME)

    def test_returns_the_same_group_on_subsequent_calls(self) -> None:
        group = AdministratorGroupService.get_or_create_group()
        self.assertEqual(AdministratorGroupService.get_or_create_group().pk, group.pk)


class AdministratorGroupServiceIsAdministratorTests(TestCase):
    def test_false_for_user_not_in_administrator_group(self) -> None:
        user = UserFactory()
        self.assertFalse(AdministratorGroupService.is_administrator(user))

    def test_true_for_user_in_administrator_group(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(AdministratorGroupService.is_administrator(user))

    def test_creates_the_group_as_a_side_effect_even_if_it_did_not_exist(self) -> None:
        user = UserFactory()
        self.assertFalse(
            Group.objects.filter(name=AdministratorGroupService.GROUP_NAME).exists()
        )
        AdministratorGroupService.is_administrator(user)
        self.assertTrue(
            Group.objects.filter(name=AdministratorGroupService.GROUP_NAME).exists()
        )

    def test_false_for_none_user(self) -> None:
        self.assertFalse(AdministratorGroupService.is_administrator(None))


class AdministratorGroupServiceAddRemoveAdministratorTests(TestCase):
    def test_add_administrator_grants_the_role(self) -> None:
        user = UserFactory()
        self.assertFalse(AdministratorGroupService.is_administrator(user))
        AdministratorGroupService.add_administrator(user)
        self.assertTrue(AdministratorGroupService.is_administrator(user))

    def test_remove_administrator_revokes_the_role(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(AdministratorGroupService.is_administrator(user))
        AdministratorGroupService.remove_administrator(user)
        self.assertFalse(AdministratorGroupService.is_administrator(user))

    def test_remove_administrator_is_safe_if_user_was_never_one(self) -> None:
        user = UserFactory()
        AdministratorGroupService.remove_administrator(user)  # must not raise
        self.assertFalse(AdministratorGroupService.is_administrator(user))
