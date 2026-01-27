"""resido URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import include, path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from common.managers.service import ServiceManager
from resido.description import DESCRIPTION

admin.site.site_title = "ResidoBackend"
admin.site.site_header = "ResidoBackend Admin"
admin.site.index_title = (
    f'Version: {ServiceManager().get_service_info().get("version")}'
)

schema_view = get_schema_view(
    openapi.Info(
        title="Resido API",
        default_version="v1",
        description=DESCRIPTION,
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # path("api/silk", include("silk.urls", namespace="silk")),
    path("admin/", admin.site.urls),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)/$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^docs/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(
        r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    re_path(r"^", include("locations.urls")),
    re_path(r"^", include("lookup.urls")),
    re_path(r"^", include("residents.urls")),
    re_path(r"^", include("staff.urls")),
    re_path(r"^", include("helixauth.urls")),
    re_path(r"^", include("notifications.urls")),
    re_path(r"^", include("common.urls")),
    re_path(r"^", include("assets.urls")),
    re_path(r"^", include("payments.urls")),
    re_path(r"^", include("meetings.urls")),
    re_path(r"^", include("audit.urls")),
    re_path(r"^", include("analytics.urls")),
    re_path(r"^", include("lease.urls")),
    re_path(r"^", include("maintenance.urls")),
    re_path(r"^", include("bookings.urls")),
    re_path(r"^", include("data.urls")),
    re_path(r"^", include("hb_core.urls")),
    re_path(r"^", include("customer_backend.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]
