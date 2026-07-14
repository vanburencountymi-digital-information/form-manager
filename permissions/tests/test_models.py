from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory
from permissions.models import AdministratorPermissions
from permissions.tests.factories import FormPermissionsFactory


def _permission_codenames(group):
    return set(group.permissions.values_list("codename", flat=True))


class FormPermissionsTests(TestCase):
    def test_created_with_no_departments_by_default(self):
        fp = FormPermissionsFactory()
        self.assertEqual(fp.editor_departments.count(), 0)
        self.assertEqual(fp.viewer_departments.count(), 0)

    def test_can_assign_editor_departments(self):
        eng = DepartmentFactory(name="Engineering")
        sales = DepartmentFactory(name="Sales")
        fp = FormPermissionsFactory(editor_departments=[eng, sales])
        self.assertEqual(fp.editor_departments.count(), 2)
        self.assertIn(eng, fp.editor_departments.all())
        self.assertIn(sales, fp.editor_departments.all())

    def test_can_assign_viewer_departments(self):
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(viewer_departments=[finance])
        self.assertEqual(fp.viewer_departments.count(), 1)
        self.assertIn(finance, fp.viewer_departments.all())

    def test_editor_and_viewer_departments_are_independent(self):
        it_dept = DepartmentFactory(name="IT")
        finance = DepartmentFactory(name="Finance")
        fp = FormPermissionsFactory(
            editor_departments=[it_dept], viewer_departments=[finance]
        )
        self.assertIn(it_dept, fp.editor_departments.all())
        self.assertNotIn(it_dept, fp.viewer_departments.all())
        self.assertIn(finance, fp.viewer_departments.all())
        self.assertNotIn(finance, fp.editor_departments.all())

    def test_a_department_can_be_both_editor_and_viewer(self):
        dept = DepartmentFactory(name="Engineering")
        fp = FormPermissionsFactory(editor_departments=[dept], viewer_departments=[dept])
        self.assertIn(dept, fp.editor_departments.all())
        self.assertIn(dept, fp.viewer_departments.all())

    def test_a_form_can_only_have_one_form_permissions_row(self):
        fp = FormPermissionsFactory()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormPermissionsFactory(form=fp.form)


class AdministratorPermissionsSyncTests(TestCase):
    def test_creates_group_if_missing(self):
        self.assertFalse(
            Group.objects.filter(name=AdministratorPermissions.GROUP_NAME).exists()
        )
        group = AdministratorPermissions.sync_permissions()
        self.assertEqual(group.name, AdministratorPermissions.GROUP_NAME)
        self.assertEqual(
            _permission_codenames(group), set(AdministratorPermissions.PERMISSION_CODENAMES)
        )

    def test_corrects_drifted_permissions(self):
        group = AdministratorPermissions.sync_permissions()
        group.permissions.clear()
        other_permission = Permission.objects.exclude(
            codename__in=AdministratorPermissions.PERMISSION_CODENAMES
        ).first()
        group.permissions.add(other_permission)

        AdministratorPermissions.sync_permissions()
        group.refresh_from_db()
        self.assertEqual(
            _permission_codenames(group), set(AdministratorPermissions.PERMISSION_CODENAMES)
        )


class AdministratorPermissionsGetOrCreateGroupTests(TestCase):
    def test_creates_group_with_permissions_synced_on_first_call(self):
        group = AdministratorPermissions.get_or_create_group()
        self.assertEqual(
            _permission_codenames(group), set(AdministratorPermissions.PERMISSION_CODENAMES)
        )

    def test_does_not_resync_permissions_on_an_existing_group(self):
        group = AdministratorPermissions.get_or_create_group()
        group.permissions.clear()

        AdministratorPermissions.get_or_create_group()
        group.refresh_from_db()
        self.assertEqual(_permission_codenames(group), set())


class AdministratorPermissionsIsAdministratorTests(TestCase):
    def test_false_for_user_not_in_administrator_group(self):
        user = UserFactory()
        self.assertFalse(AdministratorPermissions.is_administrator(user))

    def test_true_for_user_in_administrator_group(self):
        user = UserFactory(is_administrator=True)
        self.assertTrue(AdministratorPermissions.is_administrator(user))

    def test_creates_the_group_as_a_side_effect_even_if_it_did_not_exist(self):
        user = UserFactory()
        self.assertFalse(
            Group.objects.filter(name=AdministratorPermissions.GROUP_NAME).exists()
        )
        AdministratorPermissions.is_administrator(user)
        self.assertTrue(
            Group.objects.filter(name=AdministratorPermissions.GROUP_NAME).exists()
        )

class AdministratorPermissionsNotInAdminTests(TestCase):
    def test_administrator_permissions_is_not_registered_in_admin(self):
        from django.contrib import admin
        self.assertNotIn(AdministratorPermissions, admin.site._registry)
