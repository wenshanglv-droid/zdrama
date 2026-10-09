"""Isolated browser-test server. Never touches the normal dev database."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='zdrama-e2e-') as temp:
    env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.browser_test_settings',
           'DJANGO_SECRET_KEY': 'browser-test-only-not-for-deployment', 'DJANGO_DEBUG': '1',
           'E2E_DIRECTORY': temp}
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], cwd=root/'backend', env=env, check=True)
    subprocess.run([sys.executable, 'manage.py', 'shell', '-c',
        "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.create_user('e2e_staff',password='Browser-Test-Only-42!',is_staff=True); U.objects.create_user('e2e_guest',password='Browser-Test-Only-42!')"],
        cwd=root/'backend', env=env, check=True)
    subprocess.run([sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload'], cwd=root/'backend', env=env, check=True)
