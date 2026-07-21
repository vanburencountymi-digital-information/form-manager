"""
URL configuration for forms_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from accounts.forms import ActivationAwarePasswordResetForm
from accounts.views import invite_user
from core.views import landing_internal
from permissions.views import create_form_permissions, edit_form_permissions

urlpatterns = [
    path("", landing_internal, name="landing_internal"),
    # Admin's own login template only shows a "forgot password" link if a
    # URL named admin_password_reset exists — route it to our regular
    # password_reset flow instead of standing up a second one.
    path(
        "admin/password_reset/",
        RedirectView.as_view(pattern_name="password_reset"),
        name="admin_password_reset",
    ),
    path("admin/", admin.site.urls),
    re_path(r"^_nested_admin/", include("nested_admin.urls")),
    # Registered ahead of django_forms_workflows.urls below (same reason as
    # password_reset further down) — "forms/" there is an include() that
    # would otherwise swallow these first.
    path("forms/create/", create_form_permissions, name="create_form_permissions"),
    path(
        "forms/<int:form_id>/permissions/",
        edit_form_permissions,
        name="edit_form_permissions",
    ),
    path("forms/", include("django_forms_workflows.urls")),
    path("accounts/invite/", invite_user, name="invite_user"),
    # Registered ahead of django.contrib.auth.urls below so this one wins —
    # swaps in a form that also emails invited users, who start out with an
    # unusable password (see InviteUserForm) that the default
    # PasswordResetForm would otherwise silently refuse to email.
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=ActivationAwarePasswordResetForm
        ),
        name="password_reset",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("django_forms_workflows.api_urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
