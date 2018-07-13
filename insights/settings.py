"""
Django settings for insights project.

Generated by 'django-admin startproject' using Django 2.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import logging.config
import os

from logstash_formatter import LogstashFormatterV1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "bww4f_v05jj*$to3%k7i)ky0^=+radtq+n@e&g!997u+-iz%2x"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not any("KUBERNETES" in k for k in os.environ)

ALLOWED_HOSTS = ["localhost", ".insights.openshiftapps.com", "192.168.1.152"]

INTERNAL_IPS = ["127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_extensions",
    "rest_framework",
    "dynamic_rest",
    "drf_yasg",
    "inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if DEBUG:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

ROOT_URLCONF = "insights.urls"

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
            ]
        },
    }
]

WSGI_APPLICATION = "insights.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "insights"),
        "USER": os.environ.get("DB_USER", "insights"),
        "PASSWORD": os.environ.get("DB_PASS", "insights"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/tmp/static")

# Logging
# Not sure if we want to disable base django logging or not yet
LOGGING_CONFIG = None
logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "logstash": {"()": LogstashFormatterV1},
            "default": {
                "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default" if DEBUG else "logstash",
            }
        },
        "loggers": {
            "inventory": {
                "handlers": ["console"],
                "level": "DEBUG" if DEBUG else "INFO",
            },
            "django": {
                "handlers": ["console"],
                "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            },
        },
    }
)


DYNAMIC_REST = {
    # DEBUG: enable/disable internal debugging
    "DEBUG": False,
    # ENABLE_BROWSABLE_API: enable/disable the browsable API.
    # It can be useful to disable it in production.
    "ENABLE_BROWSABLE_API": True,
    # ENABLE_LINKS: enable/disable relationship links
    "ENABLE_LINKS": True,
    # ENABLE_SERIALIZER_CACHE: enable/disable caching of related serializers
    "ENABLE_SERIALIZER_CACHE": True,
    # ENABLE_SERIALIZER_OPTIMIZATIONS: enable/disable representation speedups
    "ENABLE_SERIALIZER_OPTIMIZATIONS": True,
    # DEFER_MANY_RELATIONS: automatically defer many-relations, unless
    # `deferred=False` is explicitly set on the field.
    "DEFER_MANY_RELATIONS": False,
    # MAX_PAGE_SIZE: global setting for max page size.
    # Can be overriden at the viewset level.
    "MAX_PAGE_SIZE": None,
    # PAGE_QUERY_PARAM: global setting for the pagination query parameter.
    # Can be overriden at the viewset level.
    "PAGE_QUERY_PARAM": "page",
    # PAGE_SIZE: global setting for page size.
    # Can be overriden at the viewset level.
    "PAGE_SIZE": 25,
    # PAGE_SIZE_QUERY_PARAM: global setting for the page size query parameter.
    # Can be overriden at the viewset level.
    "PAGE_SIZE_QUERY_PARAM": "per_page",
    # ADDITIONAL_PRIMARY_RESOURCE_PREFIX: String to prefix additional
    # instances of the primary resource when sideloading.
    "ADDITIONAL_PRIMARY_RESOURCE_PREFIX": "+",
    # Enables host-relative links.  Only compatible with resources registered
    # through the dynamic router.  If a resource doesn't have a canonical
    # path registered, links will default back to being resource-relative urls
    "ENABLE_HOST_RELATIVE_LINKS": True,
}