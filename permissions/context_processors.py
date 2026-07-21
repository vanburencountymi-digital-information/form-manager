from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.checks import (
    can_manage_department_users,
    can_manage_forms,
    is_a_department_owner,
    is_administrator,
)
from permissions.guards import is_authenticated_user

if TYPE_CHECKING:
    from django.http import HttpRequest


def user_roles(request: HttpRequest) -> dict[str, bool]:
    """Injects user permissions checks into the template context"""
    user = getattr(request, "user", None)
    if not is_authenticated_user(user):
        return {
            "is_a_department_owner": False,
            "is_administrator": False,
            "can_manage_forms": False,
            "can_manage_department_users": False,
        }
    return {
        "is_a_department_owner": is_a_department_owner(user),
        "is_administrator": is_administrator(user),
        "can_manage_forms": can_manage_forms(user),
        "can_manage_department_users": can_manage_department_users(user),
    }
