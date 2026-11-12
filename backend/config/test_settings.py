"""Pruebas aisladas: nunca se conectan a la base de datos del equipo."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from .settings import *  # noqa: E402,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("DOMI_TEST_DB", ":memory:")}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SECRET_KEY = "isolated-test-only-key-not-for-deployment-2026"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
