from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, override_settings

from accounts.forms import InviteUserForm
from accounts.tests.factories import UserFactory
from departments.tests.factories import DepartmentFactory

User = get_user_model()


@override_settings(USER_EMAIL_DOMAINS=["example.com", "foo.com"])
class InviteUserFormTests(TestCase):
    def setUp(self) -> None:
        self.department = DepartmentFactory(name="Engineering")
        self.inviter = UserFactory()
        self.department.owners.add(self.inviter)

    def _assemble_form(
        self, email: str = "", department=None, user=None, **extra
    ) -> None:
        data = {
            "email": email,
            "first_name": "Jane",
            "last_name": "Doe",
            "department": (department or self.department).pk,
        }
        data.update(extra)
        return InviteUserForm(
            data=data, user=user if user is not None else self.inviter
        )

    def test_valid_when_domain_is_allowlisted(self) -> None:
        form = self._assemble_form(email="jane@example.com")
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["email"], "jane@example.com")

    def test_invalid_when_domain_is_not_allowlisted(self) -> None:
        form = self._assemble_form(email="jane@not-allowed.com")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["This email domain is not allowed."])

    def test_domain_check_is_case_insensitive(self) -> None:
        form = self._assemble_form(email="Jane@EXAMPLE.COM")
        self.assertTrue(form.is_valid(), form.errors)

    def test_second_allowlisted_domain_is_accepted(self) -> None:
        form = self._assemble_form(email="jane@foo.com")
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_email_is_rejected(self) -> None:
        form = self._assemble_form(email="")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_department_is_optional(self) -> None:
        # Bypasses _assemble_form's default-department fallback deliberately
        # — passing department="" there would just fall back to
        # self.department, since "" is falsy.
        data = {
            "email": "jane@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "department": "",
        }
        form = InviteUserForm(data=data, user=self.inviter)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["department"])

    @override_settings(USER_EMAIL_DOMAINS=[])
    def test_empty_allowlist_rejects_every_domain(self) -> None:
        form = self._assemble_form(email="jane@example.com")
        self.assertFalse(form.is_valid())

    def test_invalid_when_email_already_exists_case_insensitive(self) -> None:
        User.objects.create_user(username="jane", email="jane@Example.com")
        form = self._assemble_form(email="Jane@example.com")
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_valid_when_email_does_not_already_exist(self) -> None:
        User.objects.create_user(username="someone_else", email="someone@example.com")
        form = self._assemble_form(email="jane@example.com")
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_at_150_characters_is_accepted(self) -> None:
        email = ("a" * 138) + "@example.com"  # exactly 150 characters
        self.assertEqual(len(email), 150)
        form = self._assemble_form(email=email)
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_over_150_characters_is_rejected(self) -> None:
        email = ("a" * 139) + "@example.com"  # exactly 151 characters
        self.assertEqual(len(email), 151)
        form = self._assemble_form(email=email)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_saving_adds_the_new_user_correctly(self) -> None:
        form = self._assemble_form(email="jane@example.com")
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.email, "jane@example.com")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")

    def test_non_administrator_cannot_submit_a_department_they_do_not_own(self) -> None:
        other_department = DepartmentFactory(name="Sales")
        form = self._assemble_form(
            email="jane@example.com", department=other_department
        )
        self.assertFalse(form.is_valid())
        self.assertIn("department", form.errors)

    def test_non_administrator_can_submit_a_department_they_own(self) -> None:
        form = self._assemble_form(email="jane@example.com", department=self.department)
        self.assertTrue(form.is_valid(), form.errors)


@override_settings(USER_EMAIL_DOMAINS=["example.com"])
class GetDepartmentFieldQuerysetTests(TestCase):
    """Direct, isolated tests for InviteUserForm.get_department_field_queryset."""

    def setUp(self) -> None:
        self.department = DepartmentFactory(name="Engineering")
        self.owner = UserFactory()
        self.department.owners.add(self.owner)
        # Any constructed form works as the method's `self` — the user
        # passed here doesn't affect what we call the method with below.
        self.form = InviteUserForm(user=self.owner)

    def test_returns_empty_queryset_for_none_user(self) -> None:
        result = self.form.get_department_field_queryset(None)
        self.assertEqual(list(result), [])

    def test_returns_empty_queryset_for_anonymous_user(self) -> None:
        result = self.form.get_department_field_queryset(AnonymousUser())
        self.assertEqual(list(result), [])

    def test_returns_owned_departments_for_non_administrator(self) -> None:
        result = self.form.get_department_field_queryset(self.owner)
        self.assertIn(self.department, result)

    def test_excludes_departments_the_user_does_not_own(self) -> None:
        other = DepartmentFactory(name="Sales")
        result = self.form.get_department_field_queryset(self.owner)
        self.assertNotIn(other, result)

    def test_includes_descendants_of_owned_departments(self) -> None:
        child = DepartmentFactory(name="Backend", parent=self.department)
        result = self.form.get_department_field_queryset(self.owner)
        self.assertIn(child, result)

    def test_excludes_archived_departments_for_non_administrator(self) -> None:
        self.department.archive()
        result = self.form.get_department_field_queryset(self.owner)
        self.assertNotIn(self.department, result)

    def test_returns_all_departments_for_administrator(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        unowned = DepartmentFactory(name="Sales")
        result = self.form.get_department_field_queryset(admin_user)
        self.assertIn(unowned, result)

    def test_excludes_archived_departments_for_administrator(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        self.department.archive()
        result = self.form.get_department_field_queryset(admin_user)
        self.assertNotIn(self.department, result)


@override_settings(USER_EMAIL_DOMAINS=["example.com"])
class HandleIsAdministratorFieldTests(TestCase):
    """Direct, isolated tests for InviteUserForm.handle_is_administrator_field."""

    def setUp(self) -> None:
        self.department = DepartmentFactory(name="Engineering")
        self.owner = UserFactory()
        self.department.owners.add(self.owner)

    def test_removes_the_field_for_a_non_administrator(self) -> None:
        # Constructed with an administrator so __init__ leaves the field
        # in place — isolates the removal behavior to the explicit call
        # below, rather than __init__ already having removed it.
        admin_user = UserFactory(is_administrator=True)
        form = InviteUserForm(user=admin_user)
        form.handle_is_administrator_field(self.owner)
        self.assertNotIn("is_administrator", form.fields)

    def test_removes_the_field_for_a_none_user(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        form = InviteUserForm(user=admin_user)
        form.handle_is_administrator_field(None)
        self.assertNotIn("is_administrator", form.fields)

    def test_removes_the_field_for_an_anonymous_user(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        form = InviteUserForm(user=admin_user)
        form.handle_is_administrator_field(AnonymousUser())
        self.assertNotIn("is_administrator", form.fields)

    def test_keeps_the_field_for_an_administrator(self) -> None:
        admin_user = UserFactory(is_administrator=True)
        form = InviteUserForm(user=admin_user)
        form.handle_is_administrator_field(admin_user)
        self.assertIn("is_administrator", form.fields)

    def test_safe_to_call_more_than_once_for_a_non_administrator(self) -> None:
        form = InviteUserForm(user=self.owner)  # __init__ already removed it once
        form.handle_is_administrator_field(self.owner)  # must not raise KeyError
        self.assertNotIn("is_administrator", form.fields)
