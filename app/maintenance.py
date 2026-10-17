# 文件路径：app/maintenance.py
# 保养模板数据与任务生成：按品类自动挂载保养任务
from datetime import date

from sqlalchemy.orm import Session

from app import models
from app.models import add_months

# 品类 → [(保养项目, 周期月数)]，与 docs/mvp.md 附表一致
MAINTENANCE_TEMPLATES: dict[str, list[tuple[str, int]]] = {
    "空调": [("清洗滤网", 1)],
    "冰箱": [("清洁除霜", 6)],
    "洗衣机": [("筒清洁", 3)],
    "净水器": [("更换滤芯", 6)],
    "电热水器": [("镁棒检查", 12)],
    "热水器": [("镁棒检查", 12)],
    "油烟机": [("清洗油网", 3)],
    "扫地机器人": [("耗材检查", 2)],
    "电视": [],  # 无规律保养
    # 真实家庭常见的其余品类（审计发现：电磁炉等选不了/识别不出会被静默丢成无品类）
    "电磁炉": [],
    "微波炉": [],
    "电饭煲": [],
    "电风扇": [],
}


def create_tasks_for_device(device: models.Device, db: Session) -> int:
    """按设备品类生成保养任务，返回生成条数。

    首轮 next_date = 购买日期 + 周期；若已过期则如实显示逾期，
    用户打勾完成后从当天重新起算。
    """
    templates = MAINTENANCE_TEMPLATES.get(device.category or "", [])
    if not templates or not device.purchase_date:
        return 0
    created = 0
    for title, interval in templates:
        db.add(
            models.MaintenanceTask(
                device_id=device.id,
                title=title,
                interval_months=interval,
                next_date=add_months(device.purchase_date, interval),
            )
        )
        created += 1
    db.commit()
    return created


def backfill_tasks_for_all(db: Session) -> int:
    """给已有但还没有保养任务的设备补生成任务（存量数据迁移用）"""
    total = 0
    devices = db.query(models.Device).all()
    for d in devices:
        if not d.tasks:
            total += create_tasks_for_device(d, db)
    return total
