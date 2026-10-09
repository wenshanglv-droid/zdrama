"""Start an isolated Compose project with private, per-workspace credentials."""
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.codespaces'

def prepare():
    STATE.mkdir(mode=0o700, exist_ok=True)
    STATE.chmod(0o700)
    access = STATE / 'access.json'
    if not access.exists():
        data = {key: secrets.token_urlsafe(32) for key in ['admin_password', 'recipient_password', 'secret_key', 'db_password', 'queue_password']}
        with open(access, 'x', opener=lambda p, f: os.open(p, f, 0o600)) as stream:
            json.dump(data, stream)
    data = json.loads(access.read_text())
    name = os.getenv('CODESPACE_NAME')
    domain = os.getenv('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN', 'app.github.dev')
    hostname = f'{name}-8080.{domain}' if name else '127.0.0.1'
    data['url'] = f'https://{hostname}' if name else 'http://127.0.0.1:8080'
    config = {
        'DJANGO_SECRET_KEY': data['secret_key'], 'DB_PASSWORD': data['db_password'],
        'RABBIT_PASSWORD': data['queue_password'], 'DJANGO_DEBUG': '0' if name else '1',
        'DJANGO_ALLOWED_HOSTS': f'localhost,127.0.0.1,{hostname}',
        'CSRF_TRUSTED_ORIGINS': data['url']
    }
    envfile = STATE / 'demo.env'
    with open(envfile, 'w', opener=lambda p, f: os.open(p, f, 0o600)) as stream:
        stream.write(''.join(f'{key}={value}\n' for key, value in config.items()))
    return data, config

def check_docker():
    if shutil.which('docker') is None:
        print('当前开发容器未安装Docker，系统尚未启动。\n'
              '请先执行 git pull --ff-only，然后按 Ctrl+Shift+P，选择 Codespaces: Rebuild Container。\n'
              '如果重建失败，请打开 Codespaces: View Creation Log，将末尾错误发给维护人员。\n'
              '不要删除Codespace或资料目录，也不需要手工安装Docker。', file=sys.stderr)
        return False
    if subprocess.run(['docker', 'compose', 'version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        print('缺少Docker Compose插件，请重建开发容器并检查创建日志。', file=sys.stderr)
        return False
    return True

def main():
    if not check_docker():
        raise SystemExit(2)
    data, config = prepare()
    (STATE/'ready').unlink(missing_ok=True)
    environment = {k:v for k,v in os.environ.items() if k not in config}
    compose = ['docker', 'compose', '--env-file', str(STATE/'demo.env'), '-p', 'zdrama-preview']
    for attempt in range(60):
        if subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            break
        if attempt == 59:
            raise RuntimeError('Docker未就绪。请等待启动完成后重新运行 python .devcontainer/start.py')
        time.sleep(1)
    print('正在准备剧藏网页体验，首次需下载镜像并构建，请稍候。', flush=True)
    subprocess.run(compose+['up', '-d', '--build'], cwd=ROOT, env=environment, check=True)
    subprocess.run(compose+['exec', '-T', '-e', 'ZDRAMA_DEMO=1', 'backend', 'python', 'manage.py', 'seed_demo'],
                   input=json.dumps({k:data[k] for k in ['admin_password','recipient_password']}), text=True,
                   cwd=ROOT, env=environment, check=True)
    for attempt in range(60):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8080/api/session/', timeout=2) as response:
                if response.status == 200: break
        except OSError:
            if attempt == 59: raise
            time.sleep(1)
    (STATE/'ready').write_text(data['url'])
    print('网页体验已就绪。登录信息可运行 python .devcontainer/welcome.py 查看。', flush=True)

if __name__ == '__main__':
    main()
