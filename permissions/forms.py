from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django import forms

from accounts.models import User
from departments.models import Department
from permissions.models import FormPermissions
from permissions.services.form_access_service import FormAccessService

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser


class CreateFormPermissionsForm(forms.Form):
    """Creates a brand-new FormDefinition + its FormPermissions row.
    Scopes it to the correct departments and any additional editors.
    Allows the user to explicitly grant who can view submissions.
    """

    name = forms.CharField(max_length=200, help_text="Display name for the form.")
    requires_login = forms.BooleanField(
        required=False,
        initial=True,
        label="Requires login",
        help_text="Unchecked means anyone can submit this form without an account.",
    )
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        help_text="Sets this form's editor_departments — the department(s) "
        "this form is scoped to for editing.",
    )
    editor_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        help_text="Individual users who can edit this form's structure, "
        "in addition to whoever qualifies via departments.",
    )
    submission_viewer_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        help_text="Individual users who can view every submission to this "
        "form. Nobody gets this by default, not even you — pick "
        "explicitly.",
    )

    def __init__(
        self, *args: Any, user: User | AnonymousUser | None = None, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        departments_field = cast(
            forms.ModelMultipleChoiceField, self.fields["departments"]
        )
        departments_field.queryset = FormAccessService.get_creatable_departments(user)


class EditFormPermissionsForm(forms.ModelForm):
    """Edits an existing form's FormPermissions row. submission_viewer_users
    is the only viewing grant that exists — no department-level equivalent,
    by design (see FormPermissions) — so, unlike the editor axis, there's
    nothing more to expose here for viewing than the creation flow already
    offers."""

    class Meta:
        model = FormPermissions
        fields = ["editor_departments", "editor_users", "submission_viewer_users"]
        widgets = {
            "editor_departments": forms.CheckboxSelectMultiple,
            "editor_users": forms.CheckboxSelectMultiple,
            "submission_viewer_users": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        editor_departments_field = cast(
            forms.ModelMultipleChoiceField, self.fields["editor_departments"]
        )
        editor_departments_field.queryset = Department.objects.filter(is_archived=False)
        editor_users_field = cast(
            forms.ModelMultipleChoiceField, self.fields["editor_users"]
        )
        editor_users_field.queryset = User.objects.filter(is_active=True)
        submission_viewer_users_field = cast(
            forms.ModelMultipleChoiceField, self.fields["submission_viewer_users"]
        )
        submission_viewer_users_field.queryset = User.objects.filter(is_active=True)
