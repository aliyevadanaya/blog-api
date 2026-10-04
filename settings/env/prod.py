from decouple import config

from settings.base import *

DEBUG = False

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('BLOG_POSTGRES_NAME', cast=str),
        'USER': config('BLOG_POSTGRES_USER', cast=str),
        'PASSWORD': config('BLOG_POSTGRES_PASSWORD', cast=str),
        'HOST': config('BLOG_POSTGRES_HOST', cast=str),
        'PORT': config('BLOG_POSTGRES_PORT', cast=str),
    }
}

