# API URL patterns for v1 endpoints

from django.urls import re_path
from app.views import (
    LoginView,
    EKeyListView,
    EKeyCreateView,
    EKeyDetailView,
    EKeySearchView,
)

app_name = "api_v1"

urlpatterns = [
    # Account endpoints
    re_path(r"^account/login$", LoginView.as_view(), name="login"),

    # EKey endpoints
    re_path(r"^ekeys$", EKeyListView.as_view(), name="ekey-list"),
    re_path(r"^ekeys/create", EKeyCreateView.as_view(), name="ekey-create"),
    re_path(r"^ekeys/<uuid:key_id>$", EKeyDetailView.as_view(), name="ekey-detail"),
    re_path(r"^ekeys/search$", EKeySearchView.as_view(), name="ekey-search"),
]