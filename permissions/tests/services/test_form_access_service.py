from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from accounts.tests.factories import UserFactory
from core.tests.factories import FormDefinitionFactory
from departments.models import DepartmentPermission
from departments.tests.factories import DepartmentFactory, DepartmentUserFactory
from permissions.services.form_access_service import FormAccessService
from permissions.tests.factories import FormPermissionsFactory


class FormAccessServiceCanCreateFormTests(TestCase):
    def test_true_for_administrator_with_no_department_relationship(self) -> None:
        user = UserFactory(is_administrator=True)
        dept = DepartmentFactory(name="Engineering")
        self.assertTrue(FormAccessService.can_create_form(user, dept))

    def test_true_for_department_owner(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.assertTrue(FormAccessService.can_create_form(owner, dept))

    def test_true_for_member_with_explicit_guardian_grant(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)],
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

    # No test for "explicit grant without membership" here —
    # DepartmentPermissionsService.grant_permission now enforces membership
    # at write-time (raises UserNotAMemberError otherwise, see
    # test_department_perm_service.py), and Department.remove_member
    # revokes the grant if membership is later removed — so any existing
    # grant already implies current membership. Constructing that state
    # directly via guardian's assign_perm (bypassing the service) is an
    # intentionally-unsupported shortcut, not a state this method needs to
    # defend against.

    def test_true_for_owner_without_membership(self) -> None:
        # Ownership bypasses membership entirely — same tier as
        # is_administrator. add_user_to_owners alone doesn't add
        # membership, and it doesn't need to.
        dept = DepartmentFactory(name="Engineering")
        owner = UserFactory()
        dept.add_user_to_owners(owner)
        self.assertTrue(FormAccessService.can_create_form(owner, dept))

    def test_true_for_owner_of_an_ancestor_department(self) -> None:
        parent = DepartmentFactory(name="Engineering")
        child = DepartmentFactory(name="Backend", parent=parent)
        owner = UserFactory()
        parent.add_user_to_owners(owner)
        self.assertTrue(FormAccessService.can_create_form(owner, child))

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(FormAccessService.can_create_form(AnonymousUser(), dept))

    def test_false_for_none(self) -> None:
        dept = DepartmentFactory(name="Engineering")
        self.assertFalse(FormAccessService.can_create_form(None, dept))


class FormAccessServiceCanManageFormTests(TestCase):
    def test_true_for_administrator_with_no_relationship_to_the_form(self) -> None:
        user = UserFactory(is_administrator=True)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertTrue(FormAccessService.can_manage_form(user, form_def))

    def test_true_for_direct_editor_user_grant(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_users=[user])
        self.assertTrue(FormAccessService.can_manage_form(user, form_def))

    def test_true_for_member_of_editor_department_with_can_manage_forms(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)],
        )
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(FormAccessService.can_manage_form(user, form_def))

    def test_true_for_owner_of_an_editor_department(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[dept])
        self.assertTrue(FormAccessService.can_manage_form(owner, form_def))

    def test_true_for_owner_of_an_ancestor_of_an_editor_department(self) -> None:
        parent = DepartmentUserFactory(name="Engineering")
        child = DepartmentUserFactory(name="Backend", parent=parent)
        owner = UserFactory()
        parent.add_user_to_owners(owner)
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def, editor_departments=[child])
        self.assertTrue(FormAccessService.can_manage_form(owner, form_def))

    def test_false_for_unrelated_user(self) -> None:
        user = UserFactory()
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertFalse(FormAccessService.can_manage_form(user, form_def))

    def test_false_for_anonymous_user_does_not_raise(self) -> None:
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertFalse(FormAccessService.can_manage_form(AnonymousUser(), form_def))

    def test_false_for_none(self) -> None:
        form_def = FormDefinitionFactory()
        FormPermissionsFactory(form=form_def)
        self.assertFalse(FormAccessService.can_manage_form(None, form_def))


class FormAccessServiceGetCreatableDepartmentsTests(TestCase):
    def test_administrator_gets_every_non_archived_department(self) -> None:
        admin = UserFactory(is_administrator=True)
        active = DepartmentFactory(name="Engineering")
        archived = DepartmentFactory(name="Old Team", is_archived=True)
        result = FormAccessService.get_creatable_departments(admin)
        self.assertIn(active, result)
        self.assertNotIn(archived, result)

    def test_includes_owned_departments(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_owner=owner)
        self.assertIn(dept, FormAccessService.get_creatable_departments(owner))

    def test_includes_member_department_with_explicit_grant(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(
            name="Engineering",
            with_user=user,
            with_permissions=[(user, DepartmentPermission.CAN_MANAGE_FORMS)],
        )
        self.assertIn(dept, FormAccessService.get_creatable_departments(user))

    def test_excludes_member_department_without_grant(self) -> None:
        user = UserFactory()
        dept = DepartmentUserFactory(name="Engineering", with_user=user)
        self.assertNotIn(dept, FormAccessService.get_creatable_departments(user))

    # No test for "grant without membership" here — DepartmentPermissionsService
    # .grant_permission now enforces membership at write-time (raises
    # UserNotAMemberError otherwise, see test_department_perm_service.py),
    # so get_creatable_departments doesn't need to defend against that
    # state at read-time. Constructing it directly via guardian's assign_perm
    # (bypassing the service) is an intentionally-unsupported shortcut, not
    # a state this method needs to handle.

    def test_excludes_archived_departments_even_when_owned(self) -> None:
        owner = UserFactory()
        dept = DepartmentUserFactory(
            name="Old Team", with_owner=owner, is_archived=True
        )
        self.assertNotIn(dept, FormAccessService.get_creatable_departments(owner))

    def test_empty_for_anonymous_user(self) -> None:
        DepartmentFactory(name="Engineering")
        self.assertFalse(
            FormAccessService.get_creatable_departments(AnonymousUser()).exists()
        )

    def test_empty_for_none(self) -> None:
        DepartmentFactory(name="Engineering")
        self.assertFalse(FormAccessService.get_creatable_departments(None).exists())
