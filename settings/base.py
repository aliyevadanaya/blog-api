from pathlib import Path

from django.urls import reverse_lazy

from settings.conf import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = 'settings.urls'
WSGI_APPLICATION = 'settings.wsgi.application'
ASGI_APPLICATION = 'settings.asgi.application'
AUTH_USER_MODEL = "auths.CustomUser"


# Application definition

DJANGO_AND_THIRD_PARTY_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
]

PROJECT_APPS = [
    'apps.auths.apps.AuthsConfig',
    'apps.blog.apps.BlogConfig'
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

UNFOLD = {
    "SITE_TITLE": "Blog API Admin",
    "SITE_HEADER": "Blog API",
    "SITE_SUBHEADER": "Administration",
    "SITE_SYMBOL": "article",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "oklch(97% 0.014 254.604)",
            "100": "oklch(93.2% 0.032 255.585)",
            "200": "oklch(88.2% 0.059 254.128)",
            "300": "oklch(80.9% 0.105 251.813)",
            "400": "oklch(70.7% 0.165 254.624)",
            "500": "oklch(62.3% 0.214 259.815)",
            "600": "oklch(54.6% 0.245 262.881)",
            "700": "oklch(48.8% 0.243 264.376)",
            "800": "oklch(42.4% 0.199 265.638)",
            "900": "oklch(37.9% 0.146 265.522)",
            "950": "oklch(28.2% 0.091 267.935)",
        },
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "SITE_DROPDOWN": [
        {
            "title": "GitHub",
            "icon": "code",
            "link": "https://github.com/aliyevadanaya/blog-api",
        },
        {
            "title": "Unfold documentation",
            "icon": "menu_book",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "COMMAND": {"search_models": True},
    "SIDEBAR": {
        "show_search": True,
        "navigation": "apps.blog.callbacks.sidebar_navigation",
    },
    "TABS": [{
        "models": ["blog.post"],
        "items": [
            {
                "title": "All",
                "link": reverse_lazy("admin:blog_post_changelist"),
                "active": lambda request: not request.GET.get("status__exact"),
            },
            {
                "title": "Published",
                "link": lambda request: (
                    f"{reverse_lazy('admin:blog_post_changelist')}"
                    "?status__exact=published"
                ),
                "active": lambda request: (
                    request.GET.get("status__exact") == "published"
                ),
            },
            {
                "title": "Drafts",
                "link": lambda request: (
                    f"{reverse_lazy('admin:blog_post_changelist')}"
                    "?status__exact=draft"
                ),
                "active": lambda request: (
                    request.GET.get("status__exact") == "draft"
                ),
            },
        ],
    }],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Password validation
# https://docs.djangoproject.com/en/6.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.1/howto/static-files/

STATIC_URL = 'static/'


# Email
# https://docs.djangoproject.com/en/6.1/topics/email/#topic-email-configuration

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
