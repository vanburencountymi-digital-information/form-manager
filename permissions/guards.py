from __future__ import annotations

import inspect
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User


def return_false_if_user_not_authenticated[**P](
    func: Callable[P, bool],
) -> Callable[P, bool]:
    """Wraps a permission-check function/classmethod that takes a `user`
    argument named `user` (in any position, e.g. after `cls`). Short-circuits
    to False, without calling `func`, if `user` is None, AnonymousUser, or
    otherwise not authenticated.

    Raises TypeError at decoration time (not call time) if `func` has no
    `user` parameter, since a silent miss here would otherwise make every
    call quietly return False.
    """
    signature = inspect.signature(func)
    if "user" not in signature.parameters:
        raise TypeError(
            f"{func.__qualname__} has no `user` parameter — "
            "return_false_if_user_not_authenticated requires one to check."
        )

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        bound = signature.bind(*args, **kwargs)
        user: User | AnonymousUser | None = bound.arguments.get("user")
        if not user or not user.is_authenticated:
            return False
        return func(*args, **kwargs)

    return wrapper
