from __future__ import annotations
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, _unicode_ci_compare
from django import forms
from django.conf import settings

from departments.models import Department
from permissions.checks import is_administrator

User = get_user_model()


class ActivationAwarePasswordResetForm(PasswordResetForm):
    """Identical to PasswordResetForm, except it doesn't exclude users with
    an unusable password. Invited users start out with an unusable password
    (see InviteUserForm) and rely on the password reset flow to set their
    first one, so for us "reset password" doubles as "activate account" —
    the built-in has_usable_password() filter would silently refuse to
    email them.

    CAUTION: django_forms_workflows's SSO login (sso_views.py) also gives
    users an unusable password — deliberately, since SSO-only accounts
    should never get a local one. That code path is unreachable today
    (gated behind the social_django package, which isn't installed here),
    so this is safe for now. If SSO is ever enabled, this form needs a way
    to tell "invited, not yet activated" and "SSO-only" apart before it can
    keep allowing both through."""

    def get_users(self, email):
        email_field_name = User.get_email_field_name()
        active_users = User._default_manager.filter(
            **{f"{email_field_name}__iexact": email, "is_active": True}
        )
        return (
            u
            for u in active_users
            if _unicode_ci_compare(email, getattr(u, email_field_name))
        )

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
        if not requesting_user or not requesting_user.is_authenticated:
            return Department.objects.none()
        if is_administrator(requesting_user):
            return Department.objects.filter(is_archived=False)
        return Department.get_departments_owned_by_user(requesting_user).filter(is_archived=False)

    def handle_is_administrator_field(self, requesting_user: get_user_model() = None):
        """Removes is_administrator field from form_data if the requesting user is not
        an administrator. Prevents POST hijacking."""

        if not is_administrator(requesting_user):
            self.fields.pop("is_administrator", None)
