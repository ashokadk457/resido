from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    path(
        'api/schema/',
        SpectacularAPIView.as_view(
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name='schema',
    ),

    path(
        'swagger',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
         name='swagger-ui',
    ),

    path('api/v1/', include('app.urls_v1')),
]
