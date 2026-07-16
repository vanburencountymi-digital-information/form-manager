from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.checks import (
    can_create_forms,
    can_edit_forms,
    is_a_department_owner,
    is_administrator,
)

if TYPE_CHECKING:
    from django.http import HttpRequest


def user_roles(request: HttpRequest) -> dict[str, bool]:
    """Injects user permissions checks into the template context"""
    user = getattr(request, "user", None)
    return {
        "is_a_department_owner": is_a_department_owner(user),
        "is_administrator": is_administrator(user),
        "can_create_forms": can_create_forms(user),
        "can_edit_forms": can_edit_forms(user),
    }
