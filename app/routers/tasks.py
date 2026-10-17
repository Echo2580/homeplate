# 文件路径：app/routers/tasks.py
# 保养任务接口：完成打勾 + 手动增删改（家庭真实周期和模板不一样，必须能编辑）
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device, MaintenanceTask, add_months

router = APIRouter(prefix="/api/tasks", tags=["保养任务"])


class TaskCreate(BaseModel):
    """手动新增保养任务"""
    device_id: int
    title: str = Field(max_length=100)
    interval_months: int = Field(ge=1, le=120)
    next_date: date | None = None  # 不填默认从今天起算


class TaskUpdate(BaseModel):
    """修改保养任务：项目名/周期/下次日期均可改"""
    title: str | None = Field(default=None, max_length=100)
    interval_months: int | None = Field(default=None, ge=1, le=120)
    next_date: date | None = None


def _get_task_or_404(task_id: int, db: Session) -> MaintenanceTask:
    task = db.get(MaintenanceTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="保养任务不存在")
    return task


@router.post("", summary="手动新增保养任务")
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    device = db.get(Device, data.device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    task = MaintenanceTask(
        device_id=data.device_id,
        title=data.title,
        interval_months=data.interval_months,
        next_date=data.next_date or date.today(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"ok": True, "task_id": task.id, "next_date": str(task.next_date)}


@router.patch("/{task_id}", summary="修改保养任务（项目/周期/下次日期）")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    payload = data.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="没有要修改的内容")
    for field, value in payload.items():
        setattr(task, field, value)
    # 改了周期且改的是 next_date：以填写日期为基准重排
    db.commit()
    db.refresh(task)
    return {"ok": True, "task_id": task.id, "next_date": str(task.next_date)}


@router.delete("/{task_id}", summary="删除保养任务")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
    return {"ok": True, "deleted_id": task_id}


@router.post("/{task_id}/complete", summary="完成保养，自动排下一期")
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(MaintenanceTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="保养任务不存在")
    task.last_done_at = date.today()
    task.next_date = add_months(date.today(), task.interval_months)
    db.commit()
    return {
        "ok": True,
        "task_id": task.id,
        "last_done_at": str(task.last_done_at),
        "next_date": str(task.next_date),
    }
