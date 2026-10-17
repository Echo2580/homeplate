# 文件路径：app/main.py
# FastAPI 应用入口
# 启动方式：.venv/Scripts/python.exe -m uvicorn app.main:app --reload
from fastapi import FastAPI

from app.routers import devices, pages, recognize, tasks

app = FastAPI(title="homeplate · AI 家电保养与维修助手", version="0.4.0")

app.include_router(devices.router)
app.include_router(pages.router)
app.include_router(recognize.router)
app.include_router(tasks.router)


@app.get("/", summary="健康检查")
def root():
    return {"app": "homeplate", "status": "ok", "docs": "/docs"}
