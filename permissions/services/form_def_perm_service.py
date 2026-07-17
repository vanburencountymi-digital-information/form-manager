from __future__ import annotations

from typing import TYPE_CHECKING

from permissions.checks import is_administrator
from permissions.guards import (
    assert_authenticated_user,
    return_false_if_user_not_authenticated,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User
    from departments.models import Department


class FormDefinitionPermissionsService:
    """Manages access checks for creating forms."""

    @classmethod
    @return_false_if_user_not_authenticated
    def user_can_create_form_definition(
        cls, user: User | AnonymousUser | None, department: Department
    ) -> bool:
        """True if user can create a new form for this specific department —
        administrators bypass, otherwise the user must own the department."""
        if is_administrator(user):
            return True
        user = assert_authenticated_user(user)
        return department.check_if_owned_by_user(user)
