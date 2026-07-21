from typing import TYPE_CHECKING, Any

from django.conf import settings
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
        personal_group: "PersonalGroup"

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


class PersonalGroup(Group):
    """Workaround for base django-forms-workflows package, which has several views are gated by Group membership. The PersonalGroup object allows us
    to make sure only specified users can view form submissions.

    One-to-one with User; users should always be created via UserService.create_user() or via UserFactory.
    """

    # Workaround: Explicit manager redeclaration so django-stubs doesn't reject
    # `owner` as an unexpected kwarg.
    objects = models.Manager["PersonalGroup"]()  # type: ignore[assignment,misc]

    # Named `owner`, not `user` — `user` clashes with the implicit reverse
    # relation User.groups already creates on every Group
    # (related_query_name="user", inherited down to PersonalGroup via
    # multi-table inheritance). Django's system checks reject the clash
    # (E006).
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personal_group",
    )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.name:
            self.name = f"user-{self.owner_id}"
        super().save(*args, **kwargs)
