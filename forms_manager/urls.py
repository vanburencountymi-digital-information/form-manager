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
from builder_overrides.views import (
    form_builder_api_load,
    form_builder_api_load_template,
    form_builder_api_preview,
    form_builder_api_save,
    form_builder_api_shared_list_save,
    form_builder_api_shared_lists,
    form_builder_api_templates,
    form_builder_edit,
)
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
    # Non-admin Form Builder entry view (IMPLEMENTATION_PLAN.md Phase 5) —
    # names match what the adapted template's {% url %} tags expect,
    # mirroring the package's own admin: URL names minus the namespace.
    path("forms/<int:form_id>/builder/", form_builder_edit, name="form_builder_edit"),
    path(
        "forms/builder/api/load/<int:form_id>/",
        form_builder_api_load,
        name="form_builder_api_load",
    ),
    path(
        "forms/builder/api/save/", form_builder_api_save, name="form_builder_api_save"
    ),
    path(
        "forms/builder/api/preview/",
        form_builder_api_preview,
        name="form_builder_api_preview",
    ),
    path(
        "forms/builder/api/templates/",
        form_builder_api_templates,
        name="form_builder_api_templates",
    ),
    path(
        "forms/builder/api/templates/<int:template_id>/",
        form_builder_api_load_template,
        name="form_builder_api_load_template",
    ),
    path(
        "forms/builder/api/shared-lists/",
        form_builder_api_shared_lists,
        name="form_builder_api_shared_lists",
    ),
    path(
        "forms/builder/api/shared-lists/save/",
        form_builder_api_shared_list_save,
        name="form_builder_api_shared_list_save",
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
