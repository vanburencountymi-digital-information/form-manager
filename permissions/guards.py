from __future__ import annotations

import inspect
from functools import wraps
from typing import TYPE_CHECKING

from typing_extensions import TypeIs

from accounts.models import User

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import AnonymousUser


class UnauthenticatedUserError(Exception):
    """Raised when a function that requires an already-authenticated User
    (assert_authenticated_user, or anything wrapped in
    require_authenticated_user) receives None, AnonymousUser, or an
    otherwise-unauthenticated user instead. Signals a caller bug — whoever
    called this was supposed to have already verified authentication
    (e.g. via return_false_if_user_not_authenticated or is_authenticated_user
    at a higher, boundary layer) before reaching this point."""


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
        if not is_authenticated_user(user):
            return False
        return func(*args, **kwargs)

    return wrapper


def is_authenticated_user(user: User | AnonymousUser | None) -> TypeIs[User]:
    """True if `user` is a real, logged-in user — False for None or
    AnonymousUser. Never raises either way, unlike assert_authenticated_user
    below; use this where an unauthenticated user is an expected, normal
    case to handle rather than an invariant violation.

    Typed as a TypeIs (not a plain bool), so `if not is_authenticated_user(x):
    return ...` narrows `x` to User for the rest of the function on its own —
    no separate assert_authenticated_user call needed alongside it in an
    ordinary boundary function with its own such check. assert_authenticated_user
    is still for functions with no local check of their own to narrow from
    (e.g. one already guarded by a decorator applied from the outside)."""
    return bool(user and user.is_authenticated)


def assert_authenticated_user(user: User | AnonymousUser | None) -> User:
    """Narrows `user` to a real, authenticated User, for use inside a
    function already wrapped by return_false_if_user_not_authenticated,
    right before passing `user` to something typed as User. Should be
    unreachable in normal operation, since the guard already filtered out
    anything else — raises explicitly (not a bare `assert`) so this check
    can't be silently skipped under Python's -O flag.
    """
    if not isinstance(user, User):
        raise UnauthenticatedUserError(
            f"Expected an authenticated User, got {user!r} — this should be "
            "unreachable if return_false_if_user_not_authenticated is "
            "applied correctly."
        )
    return user


def require_authenticated_user[**P](
    func: Callable[P, bool],
) -> Callable[P, bool]:
    """Wraps a permission-check function/classmethod whose `user` parameter
    is typed as a plain, authenticated User — not User | AnonymousUser |
    None. Raises UnauthenticatedUserError if `user` isn't actually one at
    runtime, since Python doesn't enforce type hints on its own.

    Use this instead of return_false_if_user_not_authenticated for internal
    helpers that should never legitimately be called with an unauthenticated
    user — a violation here means a caller skipped a check it was supposed
    to make (e.g. via is_authenticated_user/assert_authenticated_user at a
    higher, boundary layer), not a normal case to handle gracefully.

    Raises TypeError at decoration time (not call time) if `func` has no
    `user` parameter, same rationale as return_false_if_user_not_authenticated.
    """
    signature = inspect.signature(func)
    if "user" not in signature.parameters:
        raise TypeError(
            f"{func.__qualname__} has no `user` parameter — "
            "require_authenticated_user requires one to check."
        )

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> bool:
        bound = signature.bind(*args, **kwargs)
        user = bound.arguments.get("user")
        if not is_authenticated_user(user):
            raise UnauthenticatedUserError(
                f"{func.__qualname__} requires an authenticated User, got "
                f"{user!r} — the caller should have checked this first."
            )
        return func(*args, **kwargs)

    return wrapper
