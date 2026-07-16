from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from permissions.decorators import admin_or_dept_owner_required
from permissions.services.admin_group_service import AdministratorGroupService

from .forms import InviteUserForm

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@login_required
@admin_or_dept_owner_required
def invite_user(request: HttpRequest) -> HttpResponse:
    user = request.user

    if request.method == "POST":
        form = InviteUserForm(request.POST, user=user)
        if form.is_valid():
            form.instance.set_unusable_password()
            new_user = form.save()
            if form.cleaned_data.get("department"):
                form.cleaned_data["department"].add_member(new_user)
            if form.cleaned_data.get("is_administrator"):
                AdministratorGroupService.add_administrator(new_user)
            return redirect("invite_user")
    else:
        form = InviteUserForm(user=user)

    return render(request, "accounts/invite_user.html", {"form": form})
