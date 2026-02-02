import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

APP_ENV = os.getenv("APP_ENV", "dev")
load_dotenv(".env.prod" if APP_ENV == "prod" else ".env.dev")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = []
ROOT_URLCONF = 'config.urls'
TTLOCK_BASE_URL = 'https://euapi.ttlock.com'
TTLOCK={
    'CLIENT_ID': "5eb489f4b1f645d8ab7c95f7fe3e043c",
    'CLIENT_SECRET': "91e0f8fbec6a8be1ba14cb6c793635a2",
    'OAUTH_ENDPOINT': TTLOCK_BASE_URL + "/oauth2/token",
    'USER_INFO_ENDPOINT': TTLOCK_BASE_URL +'/v3/user/info',
}

INSTALLED_APPS = [
   'django.contrib.contenttypes',
    'django.contrib.auth',
    'drf_spectacular',
    'rest_framework',
    'app.apps.AppConfig',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.auth.authentication.BearerTokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'app.auth.permissions.HasBearerToken',
    ],

}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart Lock API',
    'DESCRIPTION': 'APIs for Smart Lock system',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,

    'SECURITY': [
        {'BearerAuth': []}
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
            }
        }
    },
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  
        'APP_DIRS': True, 
        'OPTIONS': {
            'context_processors': [],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    "loggers": {
        "django.db.backends": {
        "handlers": ["console"],
        "level": "DEBUG",
        }
    },
}