import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.settings")

from user_management.wsgi import application as app  # noqa: E402
