from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from accounts.services.user_service import UserService
from permissions.checks import can_manage_department_users
from permissions.guards import assert_authenticated_user

from .forms import InviteUserForm

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@login_required
def invite_user(request: HttpRequest) -> HttpResponse:
    user = assert_authenticated_user(request.user)
    if not can_manage_department_users(user):
        raise PermissionDenied

    if request.method == "POST":
        form = InviteUserForm(request.POST, user=user)
        if form.is_valid():
            UserService.create_user(
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                department=form.cleaned_data["department"],
                is_department_owner=form.cleaned_data.get("is_department_owner", False),
                can_manage_forms=form.cleaned_data.get("can_manage_forms", False),
                is_administrator=form.cleaned_data.get("is_administrator", False),
            )
            return redirect("invite_user")
    else:
        form = InviteUserForm(user=user)

    return render(request, "accounts/invite_user.html", {"form": form})
