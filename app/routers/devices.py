# 文件路径：app/routers/devices.py
# 设备档案的增删改查接口
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.maintenance import create_tasks_for_device
from app.photos import finalize_pending, remove_photo

router = APIRouter(prefix="/api/devices", tags=["设备档案"])


@router.post("", response_model=schemas.DeviceOut, summary="新增设备（自动挂保养任务）")
def create_device(data: schemas.DeviceCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    # photo_token 不是数据库字段：拿出来，等设备有 ID 后再把照片转正
    photo_token = payload.pop("photo_token", None)
    device = models.Device(**payload)
    db.add(device)
    db.commit()
    db.refresh(device)
    # 按品类自动生成保养任务（无模板的品类跳过）
    create_tasks_for_device(device, db)
    # 建档成功：铭牌照片从临时区转正为 device_{id}.jpg（无照片或 token 失效则跳过）
    photo_saved = finalize_pending(photo_token, device.id) if photo_token else None
    device.photo_saved = photo_saved  # 供前端提示"照片没存上"（查询接口恒为 None）
    return device


@router.get("", response_model=list[schemas.DeviceOut], summary="设备列表")
def list_devices(db: Session = Depends(get_db)):
    return db.query(models.Device).order_by(models.Device.id.desc()).all()


@router.get("/{device_id}", response_model=schemas.DeviceOut, summary="设备详情")
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.patch("/{device_id}", response_model=schemas.DeviceOut, summary="修改设备")
def update_device(
    device_id: int, data: schemas.DeviceUpdate, db: Session = Depends(get_db)
):
    device = db.get(models.Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    old_category = device.category
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    # 补品类是真实用户路径（AI 识别不出品类时先跳过，事后编辑补上）：
    # 品类从无到有/换新品类且当前没有任何保养任务时，按新品类补挂模板任务
    if data.category and data.category != old_category and not device.tasks:
        create_tasks_for_device(device, db)
    return device


@router.delete("/{device_id}", summary="删除设备")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(device)
    db.commit()
    # 级联清理铭牌照片，避免留下孤儿文件
    remove_photo(device_id)
    return {"ok": True, "deleted_id": device_id}
