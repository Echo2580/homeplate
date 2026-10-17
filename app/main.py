# 文件路径：app/main.py
# FastAPI 应用入口
# 日常启动：PyCharm 直接运行 run.py（带自动重载）
# 等价命令行：.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# 生产部署时不用 reload，并明确监听地址与端口
import base64
import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import devices, pages, recognize, tasks

load_dotenv()

app = FastAPI(title="homeplate · AI 家电保养与维修助手", version="0.4.0")

# 静态资源（本地化的前端依赖，见 static/js/）
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(devices.router)
app.include_router(recognize.router)
app.include_router(tasks.router)

# ---------- 访问密码保护（演示用最简方案） ----------
# .env 里配置 ACCESS_PASSWORD 后启用：整站（除 /healthz）需要输入密码
# 密码留空则不启用保护（纯本机开发时可以不配）
# 手机和电脑浏览器都会弹原生登录框，输入一次记住，无需登录页面
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "")


@app.middleware("http")
async def access_password_guard(request: Request, call_next):
    if ACCESS_PASSWORD and not request.url.path.startswith("/healthz"):
        auth = request.headers.get("Authorization", "")
        supplied = ""
        if auth.startswith("Basic "):
            try:
                _, _, supplied = base64.b64decode(auth[6:]).decode("utf-8").partition(":")
            except Exception:
                supplied = ""
        if not secrets.compare_digest(supplied, ACCESS_PASSWORD):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="homeplate"'},
            )
    response = await call_next(request)
    # 禁止浏览器缓存页面：模板更新后手机刷新即见最新版，避免旧壳子迷惑人
    response.headers["Cache-Control"] = "no-store"
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
