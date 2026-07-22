from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_forms_workflows.form_builder_views import (
    form_builder_load,
    form_builder_load_template,
    form_builder_preview,
    form_builder_templates,
    save_form_definition_from_builder_data,
    shared_option_list_api,
    shared_option_list_save,
)
from django_forms_workflows.form_builder_views import (
    form_builder_view as _form_builder_view,
)

from permissions.decorators import (
    get_manageable_form_or_403,
    require_has_manage_forms_role_anywhere,
    require_manage_permission_for_form_def,
)
from permissions.guards import assert_authenticated_user

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


@login_required
@require_manage_permission_for_form_def
def form_builder_edit(request: HttpRequest, form_id: int) -> HttpResponse:
    """Strips the `is_staff` gate from django-forms-workflows form_builder
    view via __wrapped__ and gates instead by FormAccessService.can_manage_form."""
    return _form_builder_view.__wrapped__(request, form_id=form_id)


@login_required
@require_manage_permission_for_form_def
def form_builder_api_load(request: HttpRequest, form_id: int) -> HttpResponse:
    """JSON data endpoint backing the builder — populates it with the
    form's existing fields/settings."""
    return form_builder_load.__wrapped__(request, form_id=form_id)


@login_required
@require_POST
def form_builder_api_save(request: HttpRequest) -> HttpResponse:
    """Saves builder data via save_form_definition_from_builder_data (the
    upstream-contributed helper) using `form_id` from request body to fit with
    django-forms-workflow's native form builder."""

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )

    form_id = data.get("id")
    form_name = data.get("name", "").strip()
    form_slug = data.get("slug", "").strip()
    if not form_name:
        return JsonResponse(
            {"success": False, "error": "Form name is required"}, status=400
        )
    if not form_slug:
        return JsonResponse(
            {"success": False, "error": "Form slug is required"}, status=400
        )
    if not form_id:
        return JsonResponse(
            {"success": False, "error": "form id is required"}, status=400
        )

    user = assert_authenticated_user(request.user)
    form_def = get_manageable_form_or_403(user, form_id)

    try:
        with transaction.atomic():
            form_def, field_id_mapping = save_form_definition_from_builder_data(
                data, user, form_definition=form_def
            )
    except Exception:
        logger.exception("Error saving form in builder")
        return JsonResponse(
            {"success": False, "error": "An internal error occurred."}, status=500
        )

    return JsonResponse(
        {
            "success": True,
            "form_id": form_def.id,
            "message": "Form saved successfully",
            "field_id_mapping": field_id_mapping,
        }
    )


@login_required
@require_has_manage_forms_role_anywhere
def form_builder_api_preview(request: HttpRequest) -> HttpResponse:
    """Live preview of in-progress (unsaved) builder field data — no
    specific FormDefinition involved (nothing is persisted), so gated
    existentially rather than against one form's permissions."""
    return form_builder_preview.__wrapped__(request)


@login_required
@require_has_manage_forms_role_anywhere
def form_builder_api_templates(request: HttpRequest) -> HttpResponse:
    """Lists the form template gallery — global, not form-specific."""
    return form_builder_templates.__wrapped__(request)


@login_required
@require_has_manage_forms_role_anywhere
def form_builder_api_load_template(
    request: HttpRequest, template_id: int
) -> HttpResponse:
    return form_builder_load_template.__wrapped__(request, template_id=template_id)


@login_required
@require_has_manage_forms_role_anywhere
def form_builder_api_shared_lists(request: HttpRequest) -> HttpResponse:
    """Lists shared option lists (dropdown/radio choices reusable across
    forms) — global, not form-specific."""
    return shared_option_list_api.__wrapped__(request)


@login_required
@require_has_manage_forms_role_anywhere
def form_builder_api_shared_list_save(request: HttpRequest) -> HttpResponse:
    return shared_option_list_save.__wrapped__(request)
