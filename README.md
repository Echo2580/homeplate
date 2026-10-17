# homeplate · AI 家电保养与维修助手

> 买家电是一瞬间的事，养家电是十几年的事——总得有个东西替你记着。

一个管"家电后半生"的小助手：拍一张铭牌，AI 自动识别品牌型号建档；保修期自动计算，保养任务自动排期；打开首页，哪台快过保、哪台该保养，一目了然。

**当前状态**：v0.6.0——MVP 已完成，阶段 1 体验完善进行中（铭牌照片存档已上线），电脑与手机端实测通过，公网部署准备中。

## 功能一览

### 已实现（v0.6.0）

- **📸 拍铭牌建档**——手机拍照 → 多模态大模型识别品牌/型号/序列号/品类 → 信息预填 → 确认保存，支持 AI 识别失败时手动填写
- **🖼️ 铭牌照片存档**——建档时的铭牌原图保存到服务器，详情页点开看原图；AI 识别失败走手动填写也照样留档（v0.6.0）
- **⏰ 保修时钟**——购买日期 + 保修期自动计算到期日，三色状态（🟢 在保 / 🟡 90 天内到期 / ⚪ 已过保）
- **🧼 保养排期**——按品类自动生成保养任务（空调洗滤网、净水器换滤芯、冰箱除霜…），完成打勾自动排下一期，逾期橙色示警
- **🏠 首页看板**——设备卡片流 + 统计概览（总数 / 本月待保养 / 即将过保）
- **✏️ 完整增删改**——信息编辑、设备删除（带级联任务警告与二次确认）
- **🔐 访问密码**——HTTP Basic 整站保护，公网部署即用
- **📱 手机友好**——移动端优先设计，支持 Tailscale 私有网络远程访问

### 规划中

铭牌照片存档、到期提醒推送、数据备份导出、AI 维修助手、多家庭账号、微信小程序——详见[开发路线图](docs/ROADMAP.md)。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy |
| 数据库 | MySQL 8（经 SQLAlchemy 访问） |
| 前端 | Jinja2 模板 · Tailwind CSS · Iconify（依赖已本地化到 `static/`） |
| AI 识别 | 多模态大模型直读铭牌，OpenAI 兼容端点（DeepSeek-flash / 百炼 Qwen-VL 可切换） |
| 远程访问 | Tailscale 私有组网 + HTTPS |

## 快速开始

**前提**：Python 3.12+、MySQL 8

```bash
# 1. 克隆并安装依赖
git clone https://github.com/Echo2580/homeplate.git
cd homeplate
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows

# 2. 配置环境变量
#    复制 .env.example 为 .env，填写：
#    DATABASE_URL      MySQL 连接串（建议 utf8mb4 字符集）
#    AI_API_BASE       识别模型端点（默认 DeepSeek：https://api.deepseek.com）
#    AI_API_KEY        对应 API Key
#    VISION_MODEL      视觉模型名（deepseek-flash / qwen-vl-plus）
#    ACCESS_PASSWORD   访问密码（留空则不启用保护）

# 3. 建库建表（MySQL 中先执行：CREATE DATABASE homeplate DEFAULT CHARACTER SET utf8mb4;）
.venv/Scripts/python -m app.init_db

# 4. 启动
.venv/Scripts/python run.py
```

浏览器打开 `http://127.0.0.1:8000`；同一局域网的手机访问 `http://<电脑IP>:8000`。

## 项目结构

```
app/
├── main.py            # FastAPI 入口 + /healthz 健康检查 + 访问密码中间件
├── database.py        # .env 读取 + SQLAlchemy 会话管理
├── models.py          # Device / MaintenanceTask 表 + 保修状态计算
├── schemas.py         # Pydantic 请求/响应模型
├── recognizer.py      # 铭牌识别（多模态大模型，OpenAI 兼容端点，直连绕代理）
├── photos.py          # 铭牌照片存档（临时暂存 → 建档转正 → 删除清理）
├── maintenance.py     # 品类保养模板与任务生成
└── routers/
    ├── devices.py     # 设备 CRUD API
    ├── recognize.py   # 铭牌识别 API
    ├── photos.py      # 铭牌照片上传 API
    ├── tasks.py       # 保养完成 API
    └── pages.py       # 页面路由（Jinja2 渲染）
templates/             # 四页 UI（首页 / 拍摄 / 确认 / 详情）
static/js/             # 本地化前端依赖（Tailwind · Iconify）
docs/                  # mvp.md · ROADMAP.md · devlog.md · 排障交接
```

## 版本历史

| 版本 | 内容 |
|---|---|
| v0.1.0 | 项目骨架 + 设备 CRUD API |
| v0.2.0 | 页面接入数据库真数据 + 保修三色状态 |
| v0.3.0 | 铭牌识别闭环（拍照 → AI 识别 → 建档） |
| v0.4.0 | 保养排期（品类模板挂载 + 打勾续期） |
| v0.5.0 | MVP 完成：访问密码 + 手机访问 + 识别提速 |
| v0.6.0 | 阶段 1 首项：铭牌照片存档——拍摄页暂存 → 建档转正 → 详情页展示；删除设备同步清理 |

## 文档

- [MVP 范围说明](docs/mvp.md)——做什么、不做什么、验收标准
- [开发路线图](docs/ROADMAP.md)——阶段 0/1/2 计划与技术债清单
- [开发日志](docs/devlog.md)——逐日变更与踩坑记录
