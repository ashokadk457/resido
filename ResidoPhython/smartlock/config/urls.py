from django.urls import path, include
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

app_name = "api"

urlpatterns = [
    # Root redirect to API documentation
    path("", RedirectView.as_view(url="api/docs/", permanent=False), name="root"),
    
    # Schema and documentation
    path(
        "api/schema/",
        SpectacularAPIView.as_view(
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="swagger-ui",
    ),

    # API v1 endpoints
    path("api/v1/", include("app.urls", namespace="v1")),
]
