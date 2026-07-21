from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django_forms_workflows.models import FormDefinition

from permissions.checks import can_manage_forms
from permissions.forms import CreateFormPermissionsForm, EditFormPermissionsForm
from permissions.guards import assert_authenticated_user
from permissions.services.form_access_service import FormAccessService
from permissions.services.form_permissions_service import FormPermissionsService
from permissions.utils import generate_unique_slug

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@login_required
def create_form_permissions(request: HttpRequest) -> HttpResponse:
    """Creates a new FormDefinition + its FormPermissions row — the entry
    point for making a brand-new form, before the visual builder is ever
    reached."""
    user = assert_authenticated_user(request.user)
    if not can_manage_forms(user):
        raise PermissionDenied
    if request.method == "POST":
        form = CreateFormPermissionsForm(request.POST, user=user)
        if form.is_valid():
            departments = form.cleaned_data["departments"]
            if not any(
                FormAccessService.can_create_form(user, department)
                for department in departments
            ):
                raise PermissionDenied
            form_def = FormDefinition.objects.create(
                name=form.cleaned_data["name"],
                slug=generate_unique_slug(form.cleaned_data["name"]),
                description="",
                requires_login=form.cleaned_data["requires_login"],
                created_by=user,
            )
            FormPermissionsService.create_form_permissions(
                form_def=form_def,
                editor_departments=departments,
                editor_users=form.cleaned_data["editor_users"],
                submission_viewer_users=form.cleaned_data["submission_viewer_users"],
            )
            return redirect("form_builder_edit", form_id=form_def.id)
    else:
        form = CreateFormPermissionsForm(user=user)
    return render(request, "permissions/create_form_permissions.html", {"form": form})


@login_required
def edit_form_permissions(request: HttpRequest, form_id: int) -> HttpResponse:
    """Edits an existing form's FormPermissions row — who can edit its
    schema/workflow and who can view its submissions."""
    user = assert_authenticated_user(request.user)
    form_def = get_object_or_404(FormDefinition, id=form_id)
    if not FormAccessService.can_manage_form(user, form_def):
        raise PermissionDenied
    form_permissions = form_def.permissions
    if request.method == "POST":
        form = EditFormPermissionsForm(request.POST, instance=form_permissions)
        if form.is_valid():
            FormPermissionsService.update_form_permissions(
                form_permissions,
                editor_departments=form.cleaned_data["editor_departments"],
                editor_users=form.cleaned_data["editor_users"],
                submission_viewer_users=form.cleaned_data["submission_viewer_users"],
            )
            return redirect("edit_form_permissions", form_id=form_def.id)
    else:
        form = EditFormPermissionsForm(instance=form_permissions)
    return render(
        request,
        "permissions/edit_form_permissions.html",
        {"form": form, "form_def": form_def},
    )
