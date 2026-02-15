import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment loading
APP_ENV = os.getenv("APP_ENV", "dev")
ENV_FILE = ".env.prod" if APP_ENV == "prod" else ".env.dev"
if os.path.exists(BASE_DIR / ENV_FILE):
    load_dotenv(BASE_DIR / ENV_FILE)

# Django core settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ROOT_URLCONF = "config.urls"

# Hosts and domains
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS]

# CORS configuration
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http:\/\/localhost:*([0-9]+)?$",
    r"^https:\/\/localhost:*([0-9]+)?$",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.helixbeat.com",
    "http://*.helixbeat.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Django apps configuration
INSTALLED_APPS = [
    # Django core
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",

    # Third-party apps
    "rest_framework",
    "drf_spectacular",

    # Local apps
    "app.apps.SmartLockAppConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "smartlock_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "600")),
    }
}

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# REST Framework configuration
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "app.auth.authentication.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "app.auth.permissions.HasBearerToken",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"
}

# DRF Spectacular (Swagger/OpenAPI) configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Smart Lock API",
    "DESCRIPTION": "Smart Lock API for managing digital keys",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,

    # 👇 THIS IS REQUIRED
    "SECURITY": [{"BearerAuth": []}],
}



TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

# TTLock configuration
TTLOCK_BASE_URL = os.getenv(
    "TTLOCK_BASE_URL",
    "https://euapi.ttlock.com"
)

TTLOCK = {
    "CLIENT_ID": os.getenv(
        "TTLOCK_CLIENT_ID",
        ""
    ),
    "CLIENT_SECRET": os.getenv(
        "TTLOCK_CLIENT_SECRET",
        ""
    ),
    "OAUTH_ENDPOINT": TTLOCK_BASE_URL + "/oauth2/token",
    "USER_INFO_ENDPOINT": TTLOCK_BASE_URL + "/v3/user/info",
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOGS_DIR, "smartlock.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"] if DEBUG else [],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True