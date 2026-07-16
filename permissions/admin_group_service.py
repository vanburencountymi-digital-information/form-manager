from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.models import Group

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from accounts.models import User


class AdministratorGroupService:
    """Manages the Administrator group: membership and lookups."""

    GROUP_NAME = "Administrator"

    @classmethod
    def get_or_create_group(cls) -> Group:
        """Ensures the Administrator group exists."""
        group, _ = Group.objects.get_or_create(name=cls.GROUP_NAME)
        return group

    @classmethod
    def is_administrator(cls, user: User | AnonymousUser | None) -> bool:
        """Checks if user belongs to the Administrator group. Returns `False`
        if no user."""
        if user:
            group = cls.get_or_create_group()
            return user.groups.filter(pk=group.pk).exists()
        return False

    @classmethod
    def add_administrator(cls, user: User) -> None:
        """Adds user to the Administrator group."""
        cls.get_or_create_group().user_set.add(user)

    @classmethod
    def remove_administrator(cls, user: User) -> None:
        """Removes user from the Administrator group."""
        cls.get_or_create_group().user_set.remove(user)
