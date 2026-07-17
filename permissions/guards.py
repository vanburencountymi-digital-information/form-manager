from __future__ import annotations

import inspect
from functools import wraps
from typing import TYPE_CHECKING

from accounts.models import User

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import AnonymousUser


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


def assert_authenticated_user(user: User | AnonymousUser | None) -> User:
    """Narrows `user` to a real, authenticated User, for use inside a
    function already wrapped by return_false_if_user_not_authenticated,
    right before passing `user` to something typed as User. Should be
    unreachable in normal operation, since the guard already filtered out
    anything else — raises explicitly (not a bare `assert`) so this check
    can't be silently skipped under Python's -O flag.
    """
    if not isinstance(user, User):
        raise AssertionError(
            f"Expected an authenticated User, got {user!r} — this should be "
            "unreachable if return_false_if_user_not_authenticated is "
            "applied correctly."
        )
    return user
