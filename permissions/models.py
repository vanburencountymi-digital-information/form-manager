from django.db import models

class FormPermissions(models.Model):
    class Meta:
        permissions = [
            ("can_edit_any_form", "Can edit any form, bypassing department scoping"),
        ]

    form = models.OneToOneField(
        "django_forms_workflows.FormDefinition", on_delete=models.CASCADE, related_name="permissions"
    )
    editor_departments = models.ManyToManyField(
        "departments.Department",
        related_name="editable_forms",
        blank=True,
        help_text=(
            "Departments whose members can edit this form's structure "
            "(fields, workflow, settings) in the visual builder. Does not "
            "affect who can submit the form or view its responses."
        ),
    )
    viewer_departments = models.ManyToManyField(
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
