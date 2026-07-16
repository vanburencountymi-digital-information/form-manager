from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory
from permissions.services.form_def_perm_service import FormDefinitionPermissionsService


class FormDefinitionPermissionsServiceUserCanCreateFormDefinitionTests(TestCase):
    def test_false_for_user_not_owning_the_department(self) -> None:
        user = UserFactory()
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(
            FormDefinitionPermissionsService.user_can_create_form_definition(user, dept)
        )

    def test_false_for_plain_member_who_does_not_own_the_department(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_user=user)
        self.assertFalse(
            FormDefinitionPermissionsService.user_can_create_form_definition(user, dept)
        )

    def test_true_for_owner_of_the_department(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(with_owner=user)
        self.assertTrue(
            FormDefinitionPermissionsService.user_can_create_form_definition(user, dept)
        )

    def test_false_for_owner_of_a_different_department(self) -> None:
        user = UserFactory()
        DepartmentUserFactory(with_owner=user)
        other_dept = DepartmentFactory(name="Sales")
        self.assertFalse(
            FormDefinitionPermissionsService.user_can_create_form_definition(
                user, other_dept
            )
        )

    def test_true_for_administrator_not_owning_the_department(self) -> None:
        user = UserFactory(is_administrator=True)
        dept = DepartmentFactory(name="Engineering")
        self.assertTrue(
            FormDefinitionPermissionsService.user_can_create_form_definition(user, dept)
        )

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(
            FormDefinitionPermissionsService.user_can_create_form_definition(
                AnonymousUser(), dept
            )
        )

    def test_false_for_none(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(
            FormDefinitionPermissionsService.user_can_create_form_definition(None, dept)
        )
