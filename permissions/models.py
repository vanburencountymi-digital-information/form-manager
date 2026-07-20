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
    `viewer_departments`/`viewer_users`: Who can view the form's submissions."""

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
                "Departments whose members can edit this form's structure "
                "(fields, workflow, settings) in the visual builder. Does not "
                "affect who can submit the form or view its responses."
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
    viewer_departments: models.ManyToManyField[Department, Any] = (
        models.ManyToManyField(
            "departments.Department",
            related_name="viewable_forms",
            blank=True,
            help_text=(
                "Departments whose members can view every submission to this "
                "form, at any time — independent of whether they're an "
                "assigned approver on any specific workflow stage. Does not "
                "grant edit access to the form itself."
            ),
        )
    )
    viewer_users: models.ManyToManyField[User, Any] = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="viewable_forms",
        blank=True,
        help_text=(
            "Individual users who can view every submission to this form, "
            "at any time, independent of department membership — in "
            "addition to, not instead of, whoever qualifies via "
            "viewer_departments."
        ),
    )
