"""
ASGI config for resido project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from common.managers.service import ServiceManager

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resido.settings")
ServiceManager().set_service_info_in_env_var()
application = get_asgi_application()
