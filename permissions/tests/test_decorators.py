from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase

from accounts.tests.factories import UserFactory
from permissions.decorators import administrator_required
from permissions.models import AdministratorPermissions


class AdministratorRequiredTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        @administrator_required
        def dummy_view(request):
            return "ok"

        self.dummy_view = dummy_view

    def test_denies_non_administrator(self):
        request = self.factory.get("/")
        request.user = UserFactory()
        with self.assertRaises(PermissionDenied):
            self.dummy_view(request)

    def test_allows_administrator(self):
        request = self.factory.get("/")
        request.user = UserFactory()
        AdministratorPermissions.get_or_create_group().user_set.add(request.user)
        self.assertEqual(self.dummy_view(request), "ok")
