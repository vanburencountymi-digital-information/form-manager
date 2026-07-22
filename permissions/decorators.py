from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django_forms_workflows.models import FormDefinition

from permissions.checks import can_manage_forms
from permissions.guards import assert_authenticated_user
from permissions.services.form_access_service import FormAccessService

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

    from accounts.models import User


def get_manageable_form_or_403(user: User, form_id: int) -> FormDefinition:
    """404s if no FormDefinition exists for form_id, 403s if user can't
    manage it per FormAccessService.can_manage_form. Shared by
    require_manage_permission_for_form_def below and any view (e.g.
    form_builder_api_save) that needs the fetched FormDefinition afterward,
    not just the gate."""
    form_def = get_object_or_404(FormDefinition, id=form_id)
    if not FormAccessService.can_manage_form(user, form_def):
        raise PermissionDenied
    return form_def


def require_manage_permission_for_form_def[**P](
    view_func: Callable[Concatenate[HttpRequest, int, P], HttpResponse],
) -> Callable[Concatenate[HttpRequest, int, P], HttpResponse]:
    """Gates a view keyed on a `form_id` URL kwarg: 404s if the form doesn't
    exist, 403s if the (already-authenticated, via login_required) user
    can't manage it."""

    @wraps(view_func)
    def wrapper(
        request: HttpRequest, form_id: int, *args: P.args, **kwargs: P.kwargs
    ) -> HttpResponse:
        user = assert_authenticated_user(request.user)
        get_manageable_form_or_403(user, form_id)
        return view_func(request, form_id, *args, **kwargs)

    return wrapper


def require_has_manage_forms_role_anywhere[**P](
    view_func: Callable[Concatenate[HttpRequest, P], HttpResponse],
) -> Callable[Concatenate[HttpRequest, P], HttpResponse]:
    """Gates a view with no specific form in play (a global gallery or
    preview endpoint) existentially, via checks.can_manage_forms."""

    @wraps(view_func)
    def wrapper(
        request: HttpRequest, *args: P.args, **kwargs: P.kwargs
    ) -> HttpResponse:
        user = assert_authenticated_user(request.user)
        if not can_manage_forms(user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
