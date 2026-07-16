from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied

from permissions.checks import is_a_department_owner, is_administrator

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from django.http import HttpRequest, HttpResponse


def administrator_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not is_administrator(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_or_dept_owner_required(
    view_func: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not (is_administrator(request.user) or is_a_department_owner(request.user)):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper
