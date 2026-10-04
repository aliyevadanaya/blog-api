from decouple import config

ENV_ID = config("BLOG_ENV_ID", cast=str)
SECRET_KEY = config("BLOG_SECRET_KEY", cast=str)