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
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from accounts.views import invite_user
from core.views import landing_internal

urlpatterns = [
    path("", landing_internal, name="landing_internal"),
    path('admin/', admin.site.urls),
    re_path(r'^_nested_admin/', include('nested_admin.urls')),
    path('forms/', include('django_forms_workflows.urls')),
    path("accounts/invite/", invite_user, name="invite_user"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("django_forms_workflows.api_urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


