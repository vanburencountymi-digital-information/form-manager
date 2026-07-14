from functools import wraps

from django.core.exceptions import PermissionDenied

from permissions.models import AdministratorPermissions


def administrator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not AdministratorPermissions.is_administrator(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def can_manage_departments(user):
    """True if user is an administrator, or owns at least one department.
    Guards against AnonymousUser explicitly — it isn't None, so `is None`
    doesn't catch it, and it has no owned_departments accessor the way
    it fakes .groups, so calling this on an anonymous request without
    the guard would raise AttributeError instead of returning False."""
    if not user.is_authenticated:
        return False
    return AdministratorPermissions.is_administrator(user) or user.owned_departments.exists()


def department_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not can_manage_departments(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
