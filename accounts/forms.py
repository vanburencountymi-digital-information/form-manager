from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import USER_EMAIL_DOMAINS

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data['email']

        if not email.endswith("@example.com"):
            raise forms.ValidationError(
                "Only example.com email addresses are allowed."
            )

        return email

    def email_in_allowlist(value):
        email_domain =value.split("@")[1].lower()
        
