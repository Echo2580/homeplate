# 文件路径：app/routers/pages.py
# 页面路由：渲染 Jinja2 模板（原型四页改造版）
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(tags=["页面"])
templates = Jinja2Templates(directory="templates")

# 品类 → 界面图标（mdiconify）
CATEGORY_ICONS = {
    "空调": "mdi:air-conditioner",
    "冰箱": "mdi:fridge-outline",
    "洗衣机": "mdi:washing-machine",
    "净水器": "mdi:water-outline",
    "电热水器": "mdi:water-boiler",
    "热水器": "mdi:water-boiler",
    "油烟机": "mdi:cook",
    "电视": "mdi:television",
    "扫地机器人": "mdi:robot-vacuum",
}

# 保修状态 → 界面配色（标签底色/文字色、图标底色/文字色、进度条颜色）
STATUS_STYLES = {
    "ok": {
        "tag_bg": "bg-[#E8F7F0]", "tag_text": "text-[#1FAF6B]",
        "icon_bg": "bg-[#EDF1FE]", "icon_text": "text-[#3D6DF2]",
        "bar": "bg-[#1FAF6B]",
    },
    "expiring": {
        "tag_bg": "bg-[#FFF6E6]", "tag_text": "text-[#D98A00]",
        "icon_bg": "bg-[#EDF1FE]", "icon_text": "text-[#3D6DF2]",
        "bar": "bg-[#F5A623]",
    },
    "expired": {
        "tag_bg": "bg-[#F2F3F6]", "tag_text": "text-[#8A93A5]",
        "icon_bg": "bg-[#F2F3F6]", "icon_text": "text-[#8A93A5]",
        "bar": "bg-[#D8DEE9]",
    },
    "unknown": {
        "tag_bg": "bg-[#F2F3F6]", "tag_text": "text-[#8A93A5]",
        "icon_bg": "bg-[#F2F3F6]", "icon_text": "text-[#8A93A5]",
        "bar": "bg-[#D8DEE9]",
    },
}


@router.get("/", response_class=HTMLResponse, summary="首页 · 我的家电")
def home(request: Request, db: Session = Depends(get_db)):
    devices = db.query(models.Device).order_by(models.Device.id.desc()).all()
    # "本月待保养" = 已逾期 + 未来 30 天内到期的保养任务
    due_limit = date.today() + timedelta(days=30)
    all_tasks = db.query(models.MaintenanceTask).all()
    stats = {
        "total": len(devices),
        "maintenance_due": sum(
            1 for t in all_tasks if t.next_date and t.next_date <= due_limit
        ),
        "expiring": sum(1 for d in devices if d.warranty_status == "expiring"),
    }
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "devices": devices,
            "stats": stats,
            "icons": CATEGORY_ICONS,
            "styles": STATUS_STYLES,
        },
    )


@router.get("/add", response_class=HTMLResponse, summary="添加家电 · 拍摄页")
def add_capture(request: Request):
    return templates.TemplateResponse(request, "capture.html", {})


@router.get("/add/confirm", response_class=HTMLResponse, summary="添加家电 · 确认页")
def add_confirm(request: Request):
    return templates.TemplateResponse(request, "confirm.html", {})


@router.get("/devices/{device_id}", response_class=HTMLResponse, summary="设备详情页")
def device_detail(request: Request, device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if device is None:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"device": device, "icons": CATEGORY_ICONS, "styles": STATUS_STYLES},
    )
