from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory
from permissions.services.form_access_service import FormAccessService


class FormAccessServiceCanCreateFormTests(TestCase):
    def test_true_for_administrator_with_no_department_relationship(self) -> None:
        user = UserFactory(is_administrator=True)
        dept = DepartmentFactory(name="Engineering")
        self.assertTrue(FormAccessService.can_create_form(user, dept))

    def test_true_for_department_owner(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.assertTrue(FormAccessService.can_create_form(owner, dept))

    def test_true_for_user_with_explicit_guardian_grant(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_permissions=[(user, DepartmentPermission.CAN_CREATE_FORMS)],
        )
        self.assertTrue(FormAccessService.can_create_form(user, dept))

    def test_false_for_plain_member_with_no_grant(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        self.assertFalse(FormAccessService.can_create_form(user, dept))

    def test_false_for_owner_of_a_different_department(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        owner = UserFactory()
        DepartmentUserFactory(name="Sales", with_owner=owner)
        self.assertFalse(FormAccessService.can_create_form(owner, dept))

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(FormAccessService.can_create_form(AnonymousUser(), dept))

    def test_false_for_none(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(FormAccessService.can_create_form(None, dept))
