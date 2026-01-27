"""
WSGI config for resido project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from common.managers.service import ServiceManager

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resido.settings")
ServiceManager().set_service_info_in_env_var()
application = get_wsgi_application()
