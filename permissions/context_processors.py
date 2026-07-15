from permissions.checks import is_administrator, is_department_owner


def user_roles(request):
    """Injects user permissions checks into the template context"""
    user = getattr(request, "user", None)
    return {
        "is_department_owner": is_department_owner(user),
        "is_administrator": is_administrator(user),
    }
