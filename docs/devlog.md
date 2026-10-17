# 开发日志（devlog）

> 每次变更记一笔：加了什么、改了什么、为什么。复盘就靠它。

## 2026-10-17 · 对标《新家管家》差距分析（无代码改动）

- 用户拍板方向：内容对标新家管家。产出 docs/对标新家管家-差距分析.md。
- 关键情报：新家管家是独立开发者的订阅制 App（本地存储+iCloud+DeepSeek AI），v1.0.9 上线"家庭优先级"排序（逾期维护+近期维护+保修风险合并）。
- 差距结论：①维修记录与费用（最大空白，四大主功能之一）②家庭优先级排序（纯展示层）③推送提醒（Web 限制下选 Server酱/邮件）④深色模式⑤凭证照片。
- 我方优势项：AI 拍铭牌直读、任务可编辑、免安装——保持住不丢。

## 2026-10-17 · 竞品调研（无代码改动）

- 产出 docs/竞品调研.md：海外 HomiHub（几乎同构）、国内 新家管家 / Freedom Tools·家庭维护、标杆 Centriq 关停案例、iFixit FixBot / 博西 AI 智能体等相邻玩家、Grocy/Homebox 等开源参考。
- 结论：赛道已有成熟产品，但"中文 + 免安装 Web + 拍照铭牌直读 + 保修保养一体"仍是空位；同型产品标配的"维修记录、到期提醒推送、凭证存档、导出"正是我们下一步该补的基本盘。
- 方法局限：未安装实测，商店文案与二手报道为主，已在文档第七节标明。

## 2026-10-17 · 用户实测反馈四连修（8720cfb + c655bde）

> 用户真机试用后集中反馈四个问题，全是真实使用痛点。约定补充：**用户手机是安卓，iOS 适配永久出局**。

### ① 设备名称无法自动识别 → prompt 补 name 字段
- 根因：识别 prompt 只要求品牌/型号/序列号/品类，从没要求生成"名称"——确认页名称栏只能手填（用户实际起了"2"、"6"这种名字）。
- 修复：prompt 加 name 生成规则（品牌+品类，有位置/规格信息用上，不编造）；recognize 接口返回过滤同步加 name。

### ②③ 品类太少且不能自定义 → 21 类 + 自定义输入
- 品类列表扩到 21 类（补电压力锅/热水壶/加湿器/空气净化器/取暖器/挂烫机/豆浆机/破壁机/其他），模板、AI 白名单、确认页下拉、图标映射四处同步。
- 确认页品类支持**自定义输入**：下拉选"自定义…"出输入框；AI 识别出列表外品类时自动转入自定义并预填（不再静默丢弃）。

### ④ 保养计划不能编辑 → 任务 CRUD + 详情页 UI
- 接口：POST /api/tasks（手动新增）、PATCH /api/tasks/{id}（改项目/周期/下次日期）、DELETE /api/tasks/{id}；字段校验（title≤100 字、周期 1-120 月）。
- 详情页：标题旁"＋添加"；每条任务加编辑/删除小按钮；表单支持平滑滚动定位。误触防护：删除有 confirm。

### ⑤ 铭牌照片可收起
- 详情页照片区块加"收起/展开"按钮，偏好存 localStorage（收起状态跨会话记住）。

### 验证（10/10 通过 ✓）
自定义品类建档、任务增/改/删、详情页 UI 入口齐全、周期越界 422、设备不存在 404、测试数据清理干净。
⚠️ name 识别效果需用户真机重拍验证（prompt 改动只有真实照片能检验）。

## 2026-10-17 · 体验打磨一轮：从能用到好用（审计驱动，4 个 commit）

> 用户拍板：暂停新功能，优化现有功能。方法：三名审计员并行做真实场景审计
> （报告在 .workbuddy/audit/：capture.md、home-detail.md、crosscut.md），lead 汇总去重后串行修复。
> 本轮不动数据库结构，不动 .env，全部修复独立成 commit 便于回溯。

### P0 修复
- **认证失败限速**（d895e15）：审计实测错误密码 10 次仅 7ms 全 401——公网部署时暴力破解零成本。加内存级限速：同 IP 60 秒内失败 10 次即 429（单进程有效，多 worker 部署时各算各的，演示场景够用）
- **超长字段 500**（41bf01f）：120 字设备名会穿透到 MySQL 打出裸 500 + 前端 alert 英文解析错误。schemas.py 全字段加 max_length（与 DB 列宽一致），前端 422 数组 detail 中文化兜底

### P1 修复
- **首页排序**（1242385）：原来按 id 倒序，违反 mvp.md"最快到期在前"的约定——改为按 days_left 升序、unknown 殿后
- **编辑补品类不生成任务**（41bf01f）：无品类建档是真实路径（AI 识别不出就跳过），事后编辑补品类永远没有保养任务。PATCH 时品类变化且无任务则补挂
- **品类覆盖**（41bf01f + 193a9ae）：电磁炉/微波炉/电饭煲/电风扇补进模板、AI prompt 白名单、确认页下拉、图标映射四处——审计发现 AI 返回白名单外品类会被静默丢成无品类
- **HEIC 拒收**（41bf01f）：iPhone 默认 HEIC 会被当成 .jpg 存档 → 详情页裂图。改为 400 + 可操作提示（设置→相机→格式）
- **photo_token 粘连**（193a9ae）：放弃拍摄后手动建档另一台设备，上次的照片会粘上去。进确认页无识别上下文时清残留
- **iOS 聚焦缩放**（193a9ae）：输入框 14px→16px 根治
- **静态资源缓存**（d895e15）：no-store 误伤 401KB tailwindjs，改为只对 text/html 禁缓存、/static/ 缓存一天
- **unknown 误标**（1242385）：无保修信息设备详情页显示"保修中 · 未分类"，与首页"保修期待填写"矛盾
- **移动端高度链**（193a9ae）：去掉 812px 固定高 + overflow-hidden 改自然滚动，加 viewport-fit=cover + safe-area 底部间距——长详情页的"删除设备"按钮此前可能滚不到

### P2 顺手修
- 建档响应带 photo_saved，照片没存上时前端明示；422 中文兜底；AI 报错统一说人话不透技术细节；任务"完成"加确认弹窗防误触（逾期信息重排不可逆）；任务行显示上次完成日期；进度条分母改真实天数（6 年保修原偏差 ~18%）；统计卡文案改"待保养（30 天内）"并单列逾期数；首页 N+1 用 selectinload 消除

### 验证
- 新增回归 14 项全过（限速 429/超长 422/HEIC 拒收/photo_saved/补品类挂任务/排序/缓存头/unknown 文案等）+ 照片链路 12 项回归全过
- 审计员与回归测试的临时设备均已清理，库中仅剩真实设备 #10 #11

### 已知未修（记录在案）
- 识别中无前端超时/取消按钮（AI 侧 timeout 60s）；/healthz 仍返回 app 名与 DB 状态（监控可用性优先）；编辑模式仍缺备注字段；错误页仍为裸 JSON（422/404/500）；触控目标偏小未调——下一轮候选

## 2026-10-17 · 阶段 1 首项：铭牌照片存档（v0.6.0）

### 背景
ROADMAP 阶段 1 头号功能：建档时照片此前被直接丢弃。验收标准——详情页能看到这台设备的铭牌原图。

### 新增
- `app/photos.py`：照片生命周期管理——拍摄后先存 `static/uploads/_pending/{token}.{ext}`（24 小时过期），建档成功转正为 `static/uploads/device_{id}.{ext}`；删除设备同步清理
- `app/routers/photos.py`：`POST /api/photo` 上传铭牌照片换一次性 token（校验图片类型/非空/10MB，与识别接口口径一致）
- `app/models.py`：`Device.photo_url` property（按设备 ID 查照片文件）
- 拍摄页：压缩后「上传照片」+「AI 识别」；识别失败但照片已存时提示可手动填写继续建档
- 确认页：新建时随建档请求提交 `photo_token`，保存成功后清 sessionStorage
- 详情页：「铭牌照片」区块，点图看原图
- 启动清理：服务启动时清超过 24 小时的临时照片
- `.gitignore`：`static/uploads/` 不入库（运行数据）

### 设计取舍
- **不新增数据库列**：照片按 `device_{id}.{ext}` 命名，模型 property 直接查文件——一张图不值得写迁移
- **上传与识别并行**：AI 挂了照片还在，手动兜底也能留下铭牌原图
- 兼容 jpg/png/webp/gif；前端压缩后统一 JPEG

### 验证（12/12 通过 ✓）
自动化端到端（独立端口 8001，不碰被其他项目占用的 8000）：
- `/api/photo` 返回合法 32 位 token；临时文件落盘 `_pending`
- 带 token 建档 → 照片转正 `device_{id}.png`，内容与原图逐字节一致
- 详情页渲染照片区块；照片 URL 受访问密码保护（未认证 401）
- 无效 token 不报错不崩溃（设备正常建档、无照片）；无照片手动建档正常
- 删除设备 → 照片文件同步 404；非图片上传 400 被拒

### 环境备注
- 端口 8000 被另一项目（截图转代办）的 uvicorn 占用，本轮用 8001 验证；Tailscale Serve 仍指向 127.0.0.1:8000，演示前需确认该端口由本项目占用
- 本机启动方式不变：PyCharm 跑 `run.py`（reload 监听 .py，模板改动需重启）

### 端口定案：homeplate 固定用 8001（用户拍板）
- `run.py` 端口 8000 → **8001**（8000 让给本机其他项目，避免两套服务抢端口）
- Tailscale Serve 已重新指向 `http://127.0.0.1:8001`（`tailscale serve --bg --https=443 http://127.0.0.1:8001`），手机地址不变仍为 https://desktop-8rf9pst.taild5e296.ts.net
- 注意：本机 8001 的验证实例未开 reload，PyCharm 启动前先停掉它（或换机器重启自然失效）；8001 若被占，uvicorn 会报错退出，不会抢端口

## 2026-10-17 · MVP 完成（v0.5.0）

### 手机访问打通（外部 AI 协助排查）
- 校园网（WLAN 172.24.251.35/15）下手机↔电脑直连被阻断——PktMon 实时计数证实手机流量根本没进电脑网络栈，具体阻断原因（AP 隔离/网络策略）未定案，防火墙规则无辜
- 解决方案：**Tailscale 私有组网** + Serve HTTPS（`https://desktop-8rf9pst.taild5e296.ts.net` → 127.0.0.1:8000），手机实测拍照页正常
- 完整排查记录见 `docs/交接-手机访问已打通与公网部署下一步-2026-10-17.md`

### 识别提速两连（用户实测 3 分钟 → 正常十几秒）
1. **前端压缩**（commit b0dabb9）：capture 页 canvas 缩图（最长边 1600px / JPEG 0.85），手机原图 3-8MB 砍九成，压缩失败自动回退原图
2. **直连绕代理**（commit fba2589）：识别客户端 `trust_env=False`——根因是 Clash 把 DeepSeek API 流量绕到国外再折回
- 兼容坑记录：openai 3.31 依赖 httpx2（fork）而非 httpx，http_client 参数做了双代兼容
- 全站 `Cache-Control: no-store`：修手机浏览器缓存旧模板页（"保养计划是壳子"疑云的真相——数据一直是好的，页面是旧的）

### 访问密码（commit 835703f）
- HTTP Basic 整站保护（/healthz 豁免），`.env` 的 ACCESS_PASSWORD 控制，未配置则不启用
- 四场景验证：无密码 401 弹框 / 错密码 401 / 对密码 200 / healthz 豁免 200

### MVP 状态（v0.5.0）
- 📸 家电档案（识别闭环）✅ ⏰ 保修时钟 ✅ 🧼 保养排期 ✅
- 访问密码 ✅ 手机访问 ✅ 识别速度 ✅
- **待真实验收**：家里录入 10 台+、单台 ≤30 秒、家人自助使用、公网部署（等学生机，方案已定：学生轻量机 + IP 直连 + 访问密码）

## 2026-10-17 · 部署预备三件事（接手外部 AI 交接清单）

> 背景：手机访问经 Tailscale 私有 HTTPS 打通（详见 `docs/交接-手机访问已打通与公网部署下一步-2026-10-17.md`）。本条处理交接文档第 5 节记录的"已发现、未修改"事项，均为公网部署预备工作。

### 变更
- `app/main.py`：消除 `/` 重复注册——原"健康检查 JSON"是死代码（被 pages 首页覆盖，从未生效）。改为独立 `GET /healthz`，含数据库探活（SELECT 1），供部署后监控使用
- `app/main.py`：挂载 `/static` 静态目录；启动注释与实际入口（run.py）统一
- `static/js/`：本地化前端依赖——tailwindcss.js（401KB）与 iconify-icon.min.js（22KB）从 modao.cc 下载落地，四个模板的 script 引用全部改为 `/static/js/`，模板零第三方域名依赖（公网部署后不再受 modao.cc 可达性牵制）

### 验证
- 注意：PyCharm 下 uvicorn reload 未自动重启（原因未深究），以上改动需手动重启服务生效——重启后应看到接口数 9（含 /healthz）、/static/js/ 可下载
- 重启后自查：`curl http://127.0.0.1:8000/healthz` 应返回 `{"database":"ok",...}`

## 2026-10-17 · Day 4：保养排期（MVP 三大模块收官）

### 新增
- `app/maintenance.py`：品类→保养模板映射（与 mvp.md 附表一致）+ `create_tasks_for_device`（建档自动挂任务，首轮 next_date = 购买日期 + 周期）+ `backfill_tasks_for_all`（存量设备补挂）
- `app/models.py`：新表 `MaintenanceTask`（device_id/title/interval_months/next_date/last_done_at，级联删除）；Device 加 tasks relationship 与 next_task property
- `app/routers/tasks.py`：`POST /api/tasks/{id}/complete`——完成打勾，next_date = 今天 + 周期（"自动排下一期"）
- `app/routers/devices.py`：创建设备时自动生成保养任务
- 首页统计"本月待保养"接真数据（逾期 + 30 天内到期）；首页卡片保养行接真（有任务显示"下次保养：xx · x 天后"，逾期变橙色）
- 详情页"保养计划"占位区块 → 真任务列表 + 完成按钮（fetch 后刷新页面）

### 决定
- 编辑设备时修改品类不自动重建任务（轻量版边界，记录在案）
- 首轮任务日期从购买日期起算——老设备如实显示"已逾期"，敦促补保养

### 验证（全部通过 ✓）
- 新表创建 + 存量 4 台补挂 4 条任务；用户实测建档的"客厅冰箱"（设备 6）任务已自动生成（清洁除霜 · 下次 2027-04-01）——建档自动挂任务功能被用户操作顺带验证
- 首页统计"本月待保养 3"（3 条逾期任务，来自测试数据的旧日期，符合预期）
- 完成打勾：task 1 从"已逾期 2117 天"重置为 2026-11-17（今天 + 1 个月）✓

### MVP 状态
- 📸 家电档案 ✓（识别闭环实测通过）⏰ 保修时钟 ✓ 🧼 保养排期 ✓——**三大模块代码层全部完成**
- 剩余：真实数据录入 10 台 + 手机联调（Day 5）+ 家人验收

## 2026-10-17 · Day 3：铭牌识别闭环（代码层完成）

### 新增
- `app/recognizer.py`：调阿里百炼 Qwen-VL（OpenAI 兼容模式），铭牌照片 → 结构化 JSON（品牌/型号/序列号/品类）；key 与模型名从 `.env` 读取
- `app/routers/recognize.py`：`POST /api/recognize` 接收 multipart 图片（校验类型/非空/10MB 上限），错误分级返回（400 参数 / 500 配置 / 502 调用）
- `templates/capture.html` 改造：隐藏 file input（`capture="environment"` 调起手机相机）+ 相册选择，选图即上传，识别中状态提示，成功后结果存 sessionStorage 跳确认页
- `templates/confirm.html` 改造：新增"设备名称"必填项；JS 读识别结果预填；选品类自动填默认保修月数（与 mvp.md 附表一致）；保修到期日实时预览；保存 → POST 建档 → 直接跳新设备详情页
- `.env` / `.env.example`：新增 `DASHSCOPE_API_KEY`、`QWEN_VL_MODEL`（默认 qwen-vl-plus）

### 变更
- main.py：挂载 recognize 路由，版本号 → 0.3.0
- requirements.txt：+openai、+python-multipart

### 验证（代码闭环 ✓）
- 10 个接口全部注册（含 POST /api/recognize）
- 非图片上传被 400 拒绝；拍摄页/确认页渲染正常
- ⚠️ 端到端真识别待测：需在 `.env` 填入真实 DASHSCOPE_API_KEY + 一张真实铭牌照片

### 下一步（Day 4）
- 保养排期：品类预设模板自动挂载 + 完成打勾自动排下一期 + 首页"本月待保养"统计接真
- 顺带：详情页"保养计划"占位区块替换为真数据

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
