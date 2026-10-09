# 剧藏 ZDrama — 院团数字档案

首个开发增量 v0.1。Vue 3 / TypeScript / Element Plus + Django REST Framework + PostgreSQL，Docker Compose 部署。

## 在线体验（GitHub Codespaces）

[打开网页试用环境](https://codespaces.new/wenshanglv-droid/zdrama/tree/feat/archive-foundation?quickstart=1)

1. 确认分支为 `feat/archive-foundation`，点击 **Create codespace**。
2. 等待首次构建完成，系统自动启动并准备3个虚构剧目、场次和PDF资料。
3. 终端显示当前环境的随机登录密码；账号为 `demo_admin`。未看到时运行 `python .devcontainer/welcome.py`。
4. 打开 **Ports / 端口 → 8080 → Open in Browser**，或使用自动打开的页面。

分享体验：接收账号填写 `demo_guest`，退出管理账号后使用终端显示的接收账号密码登录。端口保持Private，体验资料仅限模拟或脱敏样本。

首次创建由你在GitHub确认，使用账号的Codespaces额度；结束后在GitHub Codespaces页面停止环境。环境没有启动前，上面的链接是创建入口，不是已经运行的网站。

自动启动失败可运行 `python .devcontainer/start.py` 重试。试用使用独立的 `zdrama-preview` Compose项目、数据卷和随机密钥；不覆盖正常开发的 `.env`，再次启动不重置账号和资料。

### Codespaces提示找不到docker

这表示当前开发容器未加载Docker组件，可能尚未应用配置或创建失败进入恢复模式。

1. 终端运行 `git pull --ff-only` 获取当前开发分支更新。
2. 按 `Ctrl+Shift+P`，选择 **Codespaces: Rebuild Container**，等待重新构建。
3. 构建成功后运行 `docker --version` 和 `docker compose version`，两者均应显示版本。
4. 启动脚本会自动运行；需要重试时执行 `python .devcontainer/start.py`。
5. 如果重建失败，选择 **Codespaces: View Creation Log**，查看末尾错误。请勿删除Codespace或资料目录。

## 当前可用

- Session 登录、CSRF 校验、内部/外部账号区分。
- 创建剧目、场次，录入演职人员备注。
- 上传不超过100MB的资料，计算SHA-256，按剧目/场次/资料名搜索和分类筛选。
- 普通内部账号仅查看自己上传的资料；超级管理员查看全部。剧目和场次为内部共享基础档案。
- 单文件、不可修改原件的账号绑定分享，最长30天；接收账号验证、预览/下载权限、撤销与过期检查。
- PDF/JPG/PNG分享原件预览，其他格式可授权下载。下载流每64KB复核分享状态。
- 关键写入和资料访问审计记录。

本版本不是完整P0验收版本，也不是生产发布版本。未实现项目见 [开发计划](docs/ROADMAP.md)。特别是：尚无病毒扫描、视频转码、断点续传、细粒度部门权限、制作版本及多人演职关系、正式预览隔离和备份自动化。暂只使用可信的脱敏测试文件。

## Docker开发试用

需要Docker Engine与支持service_completed_successfully的Docker Compose v2。

```bash
cp .env.example .env
# 编辑.env，设置三个随机密码/密钥；队列密码用URL安全字符。
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py create_account archivist --internal
docker compose exec backend python manage.py create_account recipient
```

打开 http://localhost:8080 。没有默认账号或默认业务数据。演示顺序：登录内部账号 → 新建剧目 → 新建场次 → 上传PDF → 输入recipient创建分享 → 复制链接 → 退出内部账号 → 接收账号登录访问 → 原创建者撤销。

首期无需worker；后台任务服务是后续能力的部署预留，可用`docker compose --profile workers up -d`启动。尚无业务转码任务。

## 不使用Docker的本地开发

Python 3.12，Node.js 24。本地采用SQLite进行快速开发；部署使用PostgreSQL。

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
export DJANGO_SECRET_KEY='replace-with-local-random-key'
export DJANGO_DEBUG=1
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

另一个终端：

```bash
cd frontend
npm ci
npm run dev
```

Vite通过同源代理调用8000端口API，避免跨域Session问题。

## 验证

```bash
DJANGO_SECRET_KEY=test-only .venv/bin/python backend/manage.py test archive
cd frontend
npm ci
npm run build
```

后端14项测试涵盖上传校验、权限隔离、CSRF、分享接收人、账号禁用、过期、下载授权、撤销、伪造预览文件头以及传输中撤销。环境验证记录见 [VALIDATION.md](docs/VALIDATION.md)。

浏览器完整流程测试（需安装Chromium）：

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

默认使用项目根目录`.venv/bin/python`；可用`E2E_PYTHON`指定其他Python。自动创建独立临时测试数据库，启动后端和Vite，结束后清理。GitHub Actions同时验证PostgreSQL、前端、浏览器和Docker容器；最新结果查看PR #1。

## 正式部署前

当前Compose绑定127.0.0.1，只作为开发试用配置。正式部署必须完成TLS入口、关闭DEBUG、正确设置域名及CSRF来源、配置NAS持久目录和权限、备份与恢复演练，并完成开发计划中的安全验收。不要直接将此试用配置开放互联网。

容器内应用UID为10001；NAS挂载目录须允许该用户读写。原件目录不通过Nginx静态目录公开。PostgreSQL、Redis、RabbitMQ均不发布宿主机端口。预览仍会向浏览器提供文件内容，无法阻止保存或截图。

正式发布前锁定基础镜像digest；当前Dockerfile/Compose使用版本系列标签，Python与npm依赖分别由requirements.txt/package-lock.json固定。

## 源码结构

- backend/archive：业务模型、接口、权限与测试
- backend/config：Django、WSGI及Celery配置
- frontend/src：业务界面与API调用
- compose.yaml：开发试用部署
- docs：架构决策、后续任务与验证记录
