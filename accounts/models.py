from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.db import models

class User(AbstractUser):
    """Workaround implementation of email as username; preserves username field for package compatibility"""

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[EmailValidator()],
        help_text="Your email address, used to sign in.",
    )
    
    email = models.EmailField(unique=True, blank=False, max_length=150)

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        self.username = self.email
        super().save(*args, **kwargs)
