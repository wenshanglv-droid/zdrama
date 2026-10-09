"""Loaded only by scripts/e2e_server.py, with an ephemeral database and files."""
import os
from pathlib import Path
from .settings import *
DIRECTORY = Path(os.environ['E2E_DIRECTORY'])
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DIRECTORY/'test.sqlite3'}}
MEDIA_ROOT = DIRECTORY/'media'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
DEBUG = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
