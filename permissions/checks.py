from typing import TYPE_CHECKING

from permissions.models import AdministratorPermissions

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User


def is_department_owner(user: User | AnonymousUser | None) -> bool:
    """True if user directly owns at least one department. Guards against
    AnonymousUser explicitly — it isn't None, so `is None` doesn't catch it,
    and it has no owned_departments accessor the way it fakes .groups, so
    calling this on an anonymous request without the guard would raise
    AttributeError instead of returning False."""
    if not user:
        return False
    if not user.is_authenticated:
        return False
    return user.owned_departments.exists()


def is_administrator(user: User | AnonymousUser | None) -> bool:
    """True if user belongs to the Administrator group. Thin wrapper around
    AdministratorPermissions.is_administrator, kept here so every
    cross-cutting role check lives in one place."""
    return AdministratorPermissions.is_administrator(user)
