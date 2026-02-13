# API URL patterns for v1 endpoints

from django.urls import path
from app.api.views import (
    LoginView,
    EKeyListView,
    EKeyCreateView,
    EKeyDetailView,
    EKeySearchView,
)

app_name = "api_v1"

urlpatterns = [
    # Account endpoints
    path("account/login/", LoginView.as_view(), name="login"),

    # EKey endpoints
    path("ekeys/", EKeyListView.as_view(), name="ekey-list"),
    path("ekeys/create/", EKeyCreateView.as_view(), name="ekey-create"),
    path("ekeys/<uuid:key_id>/", EKeyDetailView.as_view(), name="ekey-detail"),
    path("ekeys/search/", EKeySearchView.as_view(), name="ekey-search"),
]
