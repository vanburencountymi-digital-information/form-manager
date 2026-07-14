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
