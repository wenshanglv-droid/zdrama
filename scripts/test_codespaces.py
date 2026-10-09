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
            self.assertIn('https://test-preview-8080.app.github.dev', config['CSRF_TRUSTED_ORIGINS'].split(','))
            self.assertIn('http://localhost:8080', config['CSRF_TRUSTED_ORIGINS'].split(','))
            self.assertNotIn('*', config['CSRF_TRUSTED_ORIGINS'])
            self.assertNotEqual(first['admin_password'], first['recipient_password'])

    def test_missing_docker_exits_before_changing_state(self):
        with patch.object(startup.shutil, 'which', return_value=None), patch.object(startup, 'prepare') as prepare, patch.object(startup.subprocess, 'run') as run:
            with self.assertRaises(SystemExit) as result:
                startup.main()
            self.assertEqual(result.exception.code, 2)
            prepare.assert_not_called()
            run.assert_not_called()

    def test_missing_compose_is_reported(self):
        from types import SimpleNamespace
        with patch.object(startup.shutil, 'which', return_value='/usr/bin/docker'), patch.object(startup.subprocess, 'run', return_value=SimpleNamespace(returncode=1)):
            self.assertFalse(startup.check_docker())

if __name__ == '__main__': unittest.main()
