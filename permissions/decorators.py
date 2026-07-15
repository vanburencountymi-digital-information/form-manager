from functools import wraps

from django.core.exceptions import PermissionDenied

from permissions.checks import is_administrator, is_department_owner


def administrator_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_administrator(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def department_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (is_administrator(request.user) or is_department_owner(request.user)):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
