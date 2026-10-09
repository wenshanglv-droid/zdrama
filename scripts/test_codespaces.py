import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('startup', Path(__file__).resolve().parents[1]/'.devcontainer/start.py')
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)

class CodespacesConfigTests(unittest.TestCase):
    def test_credentials_persist_privately_and_codespaces_uses_https(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(startup, 'STATE', Path(directory)/'state'), patch.dict(os.environ, {'CODESPACE_NAME':'test-preview','GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN':'app.github.dev'}):
            first, config = startup.prepare()
            second, _ = startup.prepare()
            self.assertEqual(first, second)
            self.assertEqual((startup.STATE/'access.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual((startup.STATE/'demo.env').stat().st_mode & 0o777, 0o600)
            self.assertEqual(config['DJANGO_DEBUG'], '0')
            self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], 'https://test-preview-8080.app.github.dev')
            self.assertNotEqual(first['admin_password'], first['recipient_password'])

if __name__ == '__main__': unittest.main()
