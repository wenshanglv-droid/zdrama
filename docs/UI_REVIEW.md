# 全阶段界面评审版

依据：《文艺院团数字档案系统开发需求书 V2.0》（2026-10-09）。

本次交付47个独立页面入口，覆盖P0/P1/P2业务界面及主要详情、编辑、审核、异常状态。所有新增界面均为演示，尚未接入业务后端，不代表需求已实现或通过功能验收。

## 体验入口

更新开发分支并启动服务后，从登录页或工作台点击“全功能界面预览”，或访问同一站点的 `/prototype/`。不需要业务账号；请勿输入真实密码、密钥或上传内部资料。

预览代码单独加载，无业务API调用。现有已实现系统继续使用原入口 `/`。

## 页面与需求覆盖

| 页面 | 分组 | 阶段 | 需求对应 | 路径 |
| --- | --- | --- | --- | --- |
| 工作概览 | 工作台 | P0 | WF01–03 / UI01 | `/prototype/#dashboard` |
| 消息与待办 | 工作台 | P0 | WF03 | `/prototype/#inbox` |
| 任务中心 | 工作台 | P0 | AST04 / MED02 / API01 | `/prototype/#tasks` |
| 剧目档案 | 业务档案 | P0 | REP01 | `/prototype/#productions` |
| 制作版本 | 业务档案 | P0 | REP01 | `/prototype/#editions` |
| 演出场次 | 业务档案 | P0 | EVT01 / PER01 / VEN01 | `/prototype/#events` |
| 项目与巡演 | 业务档案 | P0 | 第2章 / EVT01 | `/prototype/#projects` |
| 演职人员 | 业务档案 | P0 | PER01 | `/prototype/#people` |
| 场馆与厅室 | 业务档案 | P0 | VEN01 | `/prototype/#venues` |
| 资料中心 | 资料管理 | P0 | AST01–04 / MED01–03 / SRC01–03 | `/prototype/#assets` |
| 统一检索 | 资料管理 | P0 | SRC01–03 | `/prototype/#search` |
| 收藏与资料集 | 资料管理 | P0 | SRC03 | `/prototype/#collections` |
| 上传中心 | 资料管理 | P0 | AST01 / AST03–04 | `/prototype/#uploads` |
| 历史迁移 | 资料管理 | P0 | MIG01–04 | `/prototype/#migration` |
| 归档与清单 | 资料管理 | P0 | ARC01–02 | `/prototype/#archive` |
| 权利与授权 | 资料管理 | P0 | RGT01 | `/prototype/#rights` |
| 回收与保全 | 资料管理 | P0 | ARC03 / NEX04 | `/prototype/#recycle` |
| 分享管理 | 分享协作 | P0 + P1 | SHR01–05 / P1SHR01–04 | `/prototype/#shares` |
| 审批中心 | 分享协作 | P0 | WF02 / SHR05 / ARC03 | `/prototype/#approvals` |
| 素材征集 | 分享协作 | P1 | P1COL01–04 | `/prototype/#collection-tasks` |
| 外部分享页 | 分享协作 | P0 + P1 | UI01 / SHR02 / P1SHR01 | `/prototype/#external-share` |
| 外部投稿页 | 分享协作 | P1 | P1COL02–04 | `/prototype/#external-submit` |
| 票房台账 | 经营管理 | P0 | FIN01–03 | `/prototype/#ledger` |
| 结算与回款 | 经营管理 | P0 | FIN01 / FIN03–04 | `/prototype/#settlements` |
| 经营报表 | 经营管理 | P0 | FIN02 / FIN04 | `/prototype/#reports` |
| 多剧目分摊 | 经营管理 | P1 | P1FIN01–03 | `/prototype/#allocation` |
| 识别与转写 | 智能利用 | P1 | P1OCR01–04 / P1ASR01–04 | `/prototype/#recognition` |
| 文字对照校订 | 智能利用 | P1 | P1OCR02–04 | `/prototype/#proofread` |
| 转写与媒体标注 | 智能利用 | P1 | P1ASR02–03 / P1MED01–04 | `/prototype/#transcripts` |
| 语义检索 | 智能利用 | P2 | P2SEM01–04 | `/prototype/#semantic` |
| 档案问答 | 智能利用 | P2 | P2QA01–05 | `/prototype/#assistant` |
| 相似照片精选 | 智能利用 | P2 | P2IMG01–04 | `/prototype/#similar` |
| 艺术成果记录 | 智能利用 | P2 | P2ANN01 | `/prototype/#achievements` |
| 成果编纂 | 智能利用 | P2 | P2ANN01–05 | `/prototype/#compilations` |
| 账号与组织 | 系统管理 | P0 | SEC01–02 | `/prototype/#users` |
| 角色与权限 | 系统管理 | P0 | SEC01–02 | `/prototype/#permissions` |
| 分类与字典 | 系统管理 | P0 | 第2章 / SRC01 / API01 | `/prototype/#dictionaries` |
| 归档与审批模板 | 系统管理 | P0 | WF01–02 / ARC01 | `/prototype/#templates` |
| 统一身份 | 系统管理 | P1 | P1IAM01–04 | `/prototype/#identity` |
| 票务渠道对接 | 系统管理 | P1 | P1TKT01–04 | `/prototype/#channels` |
| 存储生命周期 | 系统管理 | P1 | P1STO01–04 | `/prototype/#storage` |
| 备份与恢复 | 系统管理 | P0 | NFR03 / TEC03 / MIG04 | `/prototype/#backups` |
| 审计与告警 | 系统管理 | P0 | NFR05 / SEC02 | `/prototype/#audit` |
| 资源与预算 | 系统管理 | P1 + P2 | NEX01–02 | `/prototype/#budgets` |
| 模型与质量治理 | 系统管理 | P2 | NEX03–05 / P2QA04 | `/prototype/#models` |
| 系统设置 | 系统管理 | P0 | NFR01–05 / TEC02 | `/prototype/#settings` |
| 界面评审清单 | 工作台 | 全阶段 | V2.0 第1–38章 | `/prototype/#review` |

## 可体验的交互

- 导航和页面直达、名称/状态筛选、分页、排序、列选择、列表/网格切换、批量选择。
- 新建/编辑表单、必要字段校验、草稿、影响确认与本地演示记录。
- 场次节目单和计划/实际阵容、归档清单、条件归档、文件版本及权利。
- 分享固定清单、审批与扩权对照、配额定义、外部接收和外部投稿状态。
- 原图/OCR文字块对照、拆分合并、转写定位及校订、图片区域标注、单源选段表单。
- 有证据/证据不足/来源冲突的固定问答示例，相似照片人工精选与拆组。
- 成果材料章节、来源核对、段落编辑与人工锁定；当前只提供演示文本导出。
- 页面顶部可切换空数据、加载、无权限、网络失败、存储不足、格式不支持、版本冲突及到期提示。
- 手机端导航、资料列表和外部分享页。

## 评审方法

1. 按实际工作顺序：剧目 → 制作版本 → 场次 → 资料 → 归档 → 分享。
2. 切换演示岗位查看财务界面与只读状态；这只展示岗位效果，不实现权限安全。
3. 检查字段命名、布局、默认值、审批节点、异常提示是否符合院团习惯。
4. 在“界面评审清单”逐页标记“需要调整”或“界面已确认”，记录意见后导出JSON。
5. 评审状态仅保存在当前浏览器，刷新保留；换设备前导出。确认记录不会自动提交给研发或触发部署。

## 边界

- 不修改后端、数据库或现有档案；不生成真实外链，不发邮件短信，不运行迁移、备份、转码或模型任务。
- 文件选择仅登记文件名及大小；不读取或上传文件内容。视频/图片为视觉示意，不是真实媒体。
- 价格、容量、任务进度、统计和来源均为虚构示例；日期范围、部分设置仅展示拟定字段。
- 演示CSV/JSON/TXT与评审记录可以下载；正式DOCX/PDF、账务和归档导出将在界面确认后实现。
- 不把“全部界面可访问”称为P0/P1/P2功能完成；后续按用户确认分批连接真实数据和实现权限、任务及第三方集成。

## 实现结构

- `frontend/src/prototype/catalog.ts`：页面目录、字段、规则及示例记录。
- `PrototypeApp.vue`：独立评审入口、导航和状态预览。
- `PageView.vue` / `DetailPanels.vue`：业务列表、表单与详情。
- `SpecialViews.vue`：工作台、外部门户、校订、标注、问答和评审。
- `store.ts`：命名隔离的浏览器演示状态及文本下载。
- `frontend/e2e/prototype.spec.ts`：页面与详情遍历、无业务API请求、表单与评审保存、手机与外部访问流程。
