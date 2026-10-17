# 文件路径：app/main.py
# FastAPI 应用入口
# 日常启动：PyCharm 直接运行 run.py（带自动重载）
# 等价命令行：.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# 生产部署时不用 reload，并明确监听地址与端口
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import get_db
from app.routers import devices, pages, recognize, tasks

app = FastAPI(title="homeplate · AI 家电保养与维修助手", version="0.4.0")

# 静态资源（本地化的前端依赖，见 static/js/）
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(devices.router)
app.include_router(recognize.router)
app.include_router(tasks.router)


@app.get("/healthz", summary="健康检查（独立于首页，含数据库探活）")
def healthz(db: Session = Depends(get_db)):
    """轻量探活：服务自身 + 数据库连通性，公网部署的监控入口"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "down"
    return {"app": "homeplate", "status": "ok", "database": db_status}
