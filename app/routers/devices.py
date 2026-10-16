# 文件路径：app/routers/devices.py
# 设备档案的增删改查接口
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/devices", tags=["设备档案"])


@router.post("", response_model=schemas.DeviceOut, summary="新增设备")
def create_device(data: schemas.DeviceCreate, db: Session = Depends(get_db)):
    device = models.Device(**data.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
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
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", summary="删除设备")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(models.Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(device)
    db.commit()
    return {"ok": True, "deleted_id": device_id}
