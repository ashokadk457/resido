"""
API Views Module - View layer that imports from controllers

This module serves as the API layer that imports controller classes
and re-exports them for URL routing. It acts as the bridge between
URLs and the modular controllers.

Architecture:
URLs → Views (imports) → Controllers (APIView classes) → Services → Repositories
"""

from app.controllers.account_controller import AccountController
from app.controllers.keys_controller import (
    EKeyListController,
    EKeyCreateController,
    EKeyDetailController,
    EKeySearchController,
)

# Account Views - imported from controllers
LoginView = AccountController

# EKey Views - imported from controllers
EKeyListView = EKeyListController
EKeyCreateView = EKeyCreateController
EKeyDetailView = EKeyDetailController
EKeySearchView = EKeySearchController

__all__ = [
    "LoginView",
    "EKeyListView",
    "EKeyCreateView",
    "EKeyDetailView",
    "EKeySearchView",
]

