from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django_forms_workflows.models import FormDefinition

from permissions.checks import can_create_forms
from permissions.forms import CreateFormPermissionsForm, EditFormPermissionsForm
from permissions.guards import assert_authenticated_user
from permissions.models import FormPermissions, apply_form_permissions
from permissions.services.form_access_service import FormAccessService
from permissions.utils import generate_unique_slug

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@login_required
def create_form_permissions(request: HttpRequest) -> HttpResponse:
    """Creates a new FormDefinition + its FormPermissions row — the entry
    point for making a brand-new form, before the visual builder is ever
    reached. Gated existentially at the view level (can this user create a
    form *somewhere*); the departments they pick are separately restricted
    to ones they qualify for via the form's own queryset. Re-checked below
    as defense in depth — the creator needs can_create_form in at least
    one selected department, not necessarily all of them: looping in an
    additional department as a co-editor doesn't grant that department
    anything new, since its members still need their own can_edit_forms
    grant to actually use it."""
    user = assert_authenticated_user(request.user)
    if not can_create_forms(user):
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
            form_permissions = FormPermissions.objects.create(form=form_def)
            form_permissions.editor_departments.set(departments)
            form_permissions.editor_users.set(form.cleaned_data["editor_users"])
            form_permissions.submission_viewer_users.set(
                form.cleaned_data["submission_viewer_users"]
            )
            apply_form_permissions(form_permissions)
            return redirect("form_builder_edit", form_id=form_def.id)
    else:
        form = CreateFormPermissionsForm(user=user)
    return render(request, "permissions/create_form_permissions.html", {"form": form})


@login_required
def edit_form_permissions(request: HttpRequest, form_id: int) -> HttpResponse:
    """Edits an existing form's FormPermissions row — who can edit its
    schema/workflow and who can view its submissions. Gated the same way
    editing the form's schema is (FormAccessService.can_edit_form):
    whoever can edit the form can also change who else can edit/view it."""
    user = assert_authenticated_user(request.user)
    form_def = get_object_or_404(FormDefinition, id=form_id)
    if not FormAccessService.can_edit_form(user, form_def):
        raise PermissionDenied
    form_permissions = form_def.permissions
    if request.method == "POST":
        form = EditFormPermissionsForm(request.POST, instance=form_permissions)
        if form.is_valid():
            form.save()
            apply_form_permissions(form_permissions)
            return redirect("edit_form_permissions", form_id=form_def.id)
    else:
        form = EditFormPermissionsForm(instance=form_permissions)
    return render(
        request,
        "permissions/edit_form_permissions.html",
        {"form": form, "form_def": form_def},
    )
