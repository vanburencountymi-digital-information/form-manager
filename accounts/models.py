from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import EmailValidator
from django.db import models

if TYPE_CHECKING:
    from django.db.models.fields.related_descriptors import RelatedManager

    from departments.models import Department


class User(AbstractUser):
    """Workaround implementation of email as username; preserves username
    field for package compatibility"""

    if TYPE_CHECKING:
        owned_departments: RelatedManager[Department]

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[EmailValidator()],
        verbose_name="email",
        help_text="Your email address, used to sign in.",
    )

    email = models.EmailField(unique=True, blank=False, max_length=150)

    # AbstractUser declares both blank=True — overridden here since every
    # User in this project should have a real name, not just an email.
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.email = self.email.lower()
        self.username = self.email
        super().save(*args, **kwargs)

    def get_or_create_personal_group(self) -> Group:
        """Returns this user's personal Group, creating it (and adding this
        user to it) on first use. On demand only — nothing creates this
        automatically at signup. For granting individual, non-department
        access to anything that only understands Group membership (e.g.
        FormDefinition.admin_groups/reviewer_groups)."""
        group, created = Group.objects.get_or_create(name=f"user-{self.pk}")
        if created:
            self.groups.add(group)
        return group
