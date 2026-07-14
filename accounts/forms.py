from __future__ import annotations
from django.contrib.auth import get_user_model
from django import forms
from django.conf import settings

from departments.models import Department
from permissions.models import AdministratorPermissions

User = get_user_model()

class InviteUserForm(forms.ModelForm):
    """Custom form for inviting users."""

    email = forms.EmailField(required=True, max_length=150)
    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        help_text="Optional — leave blank to invite someone with no department membership yet (e.g. an approver-only account).",
    )
    is_administrator = forms.BooleanField(
        required=False, label="Grant administrator access"
    )

    class Meta:
        model = User
        fields = ['email', "first_name", "last_name", "department"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["department"].queryset = self.get_department_field_queryset(user)
        self.handle_is_administrator_field(user)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        self._check_if_email_in_allowlist(email)
        return email


    def _check_if_email_in_allowlist(self, value):
        email_domain = value.split("@")[1]
        if email_domain not in settings.USER_EMAIL_DOMAINS:
            raise forms.ValidationError(
                "This email domain is not allowed."
            )

    def get_department_field_queryset(self, requesting_user: get_user_model() = None):
        """Filters the Department queryset based on the requesting user's permissions."""
        if not requesting_user:
            return Department.objects.none()
        if AdministratorPermissions.is_administrator(requesting_user):
            return Department.objects.filter(is_archived=False)
        return Department.get_departments_owned_by_user(requesting_user).filter(is_archived=False)

    def handle_is_administrator_field(self, requesting_user: get_user_model() = None):
        """Removes is_administrator field from form_data if the requesting user is not
        an administrator. Prevents POST hijacking."""

        if not AdministratorPermissions.is_administrator(requesting_user):
            self.fields.pop("is_administrator", None)
