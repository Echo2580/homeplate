# 文件路径：app/main.py
# FastAPI 应用入口
# 日常启动：PyCharm 直接运行 run.py（带自动重载）
# 等价命令行：.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# 生产部署时不用 reload，并明确监听地址与端口
import base64
import os
import secrets
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.init_db import initialize_database
from app.photos import cleanup_pending
from app.routers import devices, pages, photos, recognize, tasks

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """首次启动自动建表，并清理超期的临时铭牌照片。"""
    initialize_database()
    removed = cleanup_pending()
    if removed:
        print(f"已清理过期临时铭牌照片 {removed} 张")
    yield


app = FastAPI(
    title="homeplate · AI 家电保养与维修助手",
    version="0.6.0",
    lifespan=lifespan,
)

# 静态资源（本地化的前端依赖，见 static/js/）
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(devices.router)
app.include_router(recognize.router)
app.include_router(photos.router)
app.include_router(tasks.router)

# ---------- 访问密码保护（演示用最简方案） ----------
# .env 里配置 ACCESS_PASSWORD 后启用：整站（除 /healthz）需要输入密码
# 密码留空则不启用保护（纯本机开发时可以不配）
# 手机和电脑浏览器都会弹原生登录框，输入一次记住，无需登录页面
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "")

# ---------- 认证失败限速（内存级，单进程有效） ----------
# 审计发现：错误密码 10 次仅 7ms 全 401，公网部署时暴力破解零成本。
# 同一 IP 在 60 秒窗口内失败超过 AUTH_FAIL_LIMIT 次，直接 429 拒绝。
AUTH_FAIL_LIMIT = 10
AUTH_WINDOW_SECONDS = 60
_auth_fails: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _auth_blocked(ip: str) -> bool:
    """检查该 IP 是否已超过失败次数窗口；返回 True 表示应直接拒绝"""
    now = time.time()
    fails = [t for t in _auth_fails.get(ip, []) if now - t < AUTH_WINDOW_SECONDS]
    _auth_fails[ip] = fails  # 顺手清掉窗口外的旧记录
    return len(fails) >= AUTH_FAIL_LIMIT


def _record_auth_fail(ip: str) -> None:
    _auth_fails.setdefault(ip, []).append(time.time())


@app.middleware("http")
async def access_password_guard(request: Request, call_next):
    if ACCESS_PASSWORD and not request.url.path.startswith("/healthz"):
        ip = _client_ip(request)
        if _auth_blocked(ip):
            return Response(
                status_code=429,
                content="尝试次数过多，请 1 分钟后再试",
                media_type="text/plain; charset=utf-8",
            )
        auth = request.headers.get("Authorization", "")
        supplied = ""
        if auth.startswith("Basic "):
            try:
                _, _, supplied = base64.b64decode(auth[6:]).decode("utf-8").partition(":")
            except Exception:
                supplied = ""
        if not secrets.compare_digest(supplied, ACCESS_PASSWORD):
            _record_auth_fail(ip)
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="homeplate"'},
            )
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("text/html"):
        # 只禁缓存页面：模板更新后手机刷新即见最新版，避免旧壳子迷惑人
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/static/"):
        # 静态资源（tailwindjs 401KB 等）允许缓存一天：省手机流量，加载更快
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response


@app.get("/healthz", summary="健康检查（独立于首页，含数据库探活）")
def healthz(db: Session = Depends(get_db)):
    """轻量探活：服务自身 + 数据库连通性，公网部署的监控入口"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "down"
    return {"app": "homeplate", "status": "ok", "database": db_status}
