# 文件路径：app/routers/tasks.py
# 保养任务接口：完成打勾，自动排下一期
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MaintenanceTask, add_months

router = APIRouter(prefix="/api/tasks", tags=["保养任务"])


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
