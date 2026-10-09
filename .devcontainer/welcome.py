import json
from pathlib import Path
root = Path(__file__).resolve().parents[1] / '.codespaces'
if not (root/'ready').exists():
    print('系统正在准备。完成后运行：python .devcontainer/welcome.py')
else:
    data=json.loads((root/'access.json').read_text())
    print('\n剧藏网页体验已就绪\n网址：'+(root/'ready').read_text())
    print('管理账号：demo_admin\n密码：'+data['admin_password'])
    print('\n分享接收账号：demo_guest\n密码：'+data['recipient_password'])
    print('\n密码只属于当前试用环境，请勿提交或对外分享。')
    print('浏览器未自动打开时，请在Ports/端口面板打开8080。端口保持Private。\n')
