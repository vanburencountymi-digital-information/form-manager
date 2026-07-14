from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from permissions.decorators import department_manager_required
from permissions.models import AdministratorPermissions

from .forms import InviteUserForm


@login_required
@department_manager_required
def invite_user(request):
    user = request.user

    if request.method == "POST":
        form = InviteUserForm(request.POST, user=user)
        if form.is_valid():
            new_user = form.save()
            if form.cleaned_data.get("department"):
                form.cleaned_data["department"].add_member(new_user)
            if form.cleaned_data.get("is_administrator"):
                new_user.groups.add(AdministratorPermissions.get_or_create_group())
            return redirect("invite_user")
    else:
        form = InviteUserForm(user=user)

    return render(request, "accounts/invite_user.html", {"form": form})
