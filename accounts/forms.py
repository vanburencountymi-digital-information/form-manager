from django import forms
from django.conf import settings
from django.contrib.auth.models import User

class InviteUserForm(forms.ModelForm):
    """Custom form for inviting users."""

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email', "first_name", "last_name"]


    def clean_email(self):
        email = self.cleaned_data['email']
        self.check_if_email_in_allowlist(email)
        return email


    def check_if_email_in_allowlist(self, value):
        email_domain = value.split("@")[1].lower()
        if email_domain not in settings.USER_EMAIL_DOMAINS:
            raise forms.ValidationError(
                "This email domain is not allowed."
            )

