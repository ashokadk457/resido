# API URL patterns for v1 endpoints

from django.urls import re_path
from app.views import (
    LoginView
)

app_name = "api_v1"

urlpatterns = [
    # Account endpoints
    re_path(r"^account/login$", LoginView.as_view(), name="login")
]