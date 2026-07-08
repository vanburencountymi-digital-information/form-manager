from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class InviteUserForm(forms.ModelForm):
    """Custom form for inviting users."""

    email = forms.EmailField(required=True, max_length=150)

    class Meta:
        model = User
        fields = ['email', "first_name", "last_name"]


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
