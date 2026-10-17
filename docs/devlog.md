# 开发日志（devlog）

> 每次变更记一笔：加了什么、改了什么、为什么。复盘就靠它。

## 2026-10-17 · Day 2：页面接入真数据 + 保修状态计算

### 新增
- `templates/` 四页：home.html（Jinja2 改造，真数据循环 + 统计卡）、detail.html（真数据 + 保修进度条）、capture.html / confirm.html（原型静态页清洗墨刀脚本后挂载）
- `app/routers/pages.py`：页面路由（`/` 首页、`/add` 拍摄、`/add/confirm` 确认、`/devices/{id}` 详情，不存在的设备 302 回首页）
- `app/models.py`：purchase_date 改为 Date 类型；新增保修计算 property（warranty_end / days_left / warranty_status / warranty_label / warranty_progress）
- 保修三色规则：剩余 >90 天在保绿 / ≤90 天即将到期黄 / <0 已过保灰
- `STATUS_STYLES` / `CATEGORY_ICONS`：状态配色与品类图标映射（pages.py 内）

### 变更
- MySQL 迁移：devices.purchase_date VARCHAR(20) → DATE（ALTER TABLE，数据无损）
- schemas.py：purchase_date 类型 str → date
- main.py：挂载 pages 路由，应用版本号 → 0.2.0
- requirements.txt：+jinja2

### 验证（全部通过 ✓）
- 首页渲染 4 台真设备：客厅空调黄"保修剩 44 天" / 净水器绿"8 个月" / 冰箱绿"12 个月" / 洗衣机灰"已过保"
- 空调显示 44 天（原型是 45 天）——日期过了一天自动变，真数据的活证
- 详情页进度条 2%（44 ÷ 2160 天）、404 重定向、拍摄页渲染均 OK
- 修正两条测试数据日期（净水器 → 2026-06-15、冰箱 → 2024-10-17），使状态与原型对齐

### 下一步（Day 3）
- 拍铭牌 → Qwen-VL 识别 → 建档闭环（MVP 灵魂）
- 测试粮草：真实铭牌照片 10 张（大哥负责攒）

## 2026-10-16 · Day 1：项目骨架

### 新增
- `app/main.py`：FastAPI 入口，健康检查路由 `/`
- `app/database.py`：从 `.env` 读 MySQL 连接串；`get_db` 依赖（每请求一会话，自动关闭）
- `app/models.py`：`Device` 设备表（名称/品牌/型号/序列号/品类/购买日期/保修月数/备注）
- `app/schemas.py`：Pydantic 请求/响应模型（Create / Update / Out）
- `app/routers/devices.py`：设备增删改查 API（`/api/devices`）
- `app/init_db.py`：建表脚本（`python -m app.init_db`）
- `.env.example` + `.env`（占位）：数据库连接配置；**`.env` 已被 .gitignore 挡住，不进仓库**
- `requirements.txt`：fastapi / uvicorn / sqlalchemy / pymysql / cryptography / python-dotenv

### 决定
- 数据库用 **MySQL**（本地已有环境），经 SQLAlchemy 访问——后续换库只需改 `.env` 里的连接串
- 建表用独立脚本 `init_db.py`，不用启动时自动建表：服务启动不依赖数据库是否在线

### 安全
- 数据库密码只存 `.env`（被 .gitignore 挡住），仓库里只有 `.env.example` 模板

### 下一步（Day 2）
- 原型四页改造为 Jinja2 模板，首页设备列表接真数据

### 待办 / 待验证（2026-10-16 23:25 全部通过 ✓）
- [x] MySQL 里已创建 `homeplate` 库（utf8mb4）
- [x] `.env` 已填真实密码
- [x] `python -m app.init_db` 建表成功
- [x] CRUD 全链路实测通过：新增 4 台设备（客厅空调/净水器/冰箱/洗衣机，中文无乱码）→ 列表查询 → PATCH 修改备注 → DELETE 删除临时设备 → 404 异常处理
- 库里已留 4 台真实设备数据，Day 2 首页接真数据时直接使用
