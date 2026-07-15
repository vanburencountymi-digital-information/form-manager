from django.test import TestCase

from accounts.tests.factories import UserFactory
from permissions.models import AdministratorPermissions


class UserFactoryIsAdministratorTests(TestCase):
    def test_not_an_administrator_by_default(self) -> None:
        user = UserFactory()
        self.assertFalse(AdministratorPermissions.is_administrator(user))

    def test_is_administrator_true_grants_the_role(self) -> None:
        user = UserFactory(is_administrator=True)
        self.assertTrue(AdministratorPermissions.is_administrator(user))
