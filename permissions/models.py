from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models

if TYPE_CHECKING:
    from accounts.models import User
    from departments.models import Department


class FormPermissions(models.Model):
    """Sets FormDefinition permissions.
    `editor_departments`/`editor_users`: Who can edit the form schema.
    `submission_viewer_users`: Who can view the form's submissions. Deliberately
    individual-only, no department-level equivalent — viewing submission
    data is the one axis that stays strictly least-privilege, explicit-
    grant-per-person, never extended by department or hierarchy
    membership."""

    form = models.OneToOneField(
        "django_forms_workflows.FormDefinition",
        on_delete=models.CASCADE,
        related_name="permissions",
    )

    def __str__(self) -> str:
        return f"{self.form.name} permissions"

    editor_departments: models.ManyToManyField[Department, Any] = (
        models.ManyToManyField(
            "departments.Department",
            related_name="editable_forms",
            blank=True,
            help_text=(
                "Members of the selected departments that have been assigned the "
                "blanket `Can edit forms` permissions will be able to edit this form. "
                "Leave this blank if you don't want any blanket permissions added to this form."
            ),
        )
    )
    editor_users: models.ManyToManyField[User, Any] = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="editable_forms",
        blank=True,
        help_text=(
            "Individual users who can edit this form's structure, "
            "independent of department membership — in addition to, not "
            "instead of, whoever qualifies via editor_departments."
        ),
    )
    submission_viewer_users: models.ManyToManyField[User, Any] = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="viewable_forms",
        blank=True,
        help_text=(
            "Individual users who can view every submission to this "
            "form, at any time. Nobody gets this via department "
            "membership, no matter how the form is scoped for editing "
            "— an explicit, minimum-necessary, per-person grant only."
        ),
    )
