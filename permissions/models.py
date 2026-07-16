from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import models

if TYPE_CHECKING:
    from departments.models import Department


class FormPermissions(models.Model):
    """Sets FormDefinition permissions.
    `editor_departments`: Who can edit the form schema.
    `viewer_departments`: Who can view for the form submissions."""

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
