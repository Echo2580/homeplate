# 文件路径：app/models.py
# 数据库表模型：设备档案（含保修状态计算）+ 保养任务
import calendar
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.photos import photo_url as _device_photo_url


def add_months(d: date, months: int) -> date:
    """日期加 N 个月（自动处理月末：1 月 31 日加 1 个月 = 2 月 28 日）"""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class Device(Base):
    """家电设备档案表：一台设备一条记录"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="设备名称，如：客厅空调")
    brand = Column(String(50), comment="品牌，如：格力")
    model_name = Column(String(100), comment="型号，如：KFR-35GW")
    serial_number = Column(String(100), comment="序列号（铭牌上识别）")
    category = Column(String(50), comment="品类：空调/冰箱/洗衣机/净水器...")
    purchase_date = Column(Date, comment="购买日期")
    warranty_months = Column(Integer, comment="保修期（月），按品类默认值可改")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # ---------- 保修状态计算（页面与接口共用的展示逻辑） ----------

    @property
    def warranty_end(self) -> date | None:
        """保修到期日 = 购买日期 + 保修月数"""
        if self.purchase_date is None or not self.warranty_months:
            return None
        return add_months(self.purchase_date, self.warranty_months)

    @property
    def days_left(self) -> int | None:
        """距离保修到期的天数，负数表示已过保"""
        end = self.warranty_end
        if end is None:
            return None
        return (end - date.today()).days

    @property
    def warranty_status(self) -> str:
        """三色状态：ok 在保 / expiring 90 天内到期 / expired 已过保 / unknown 信息不全"""
        dl = self.days_left
        if dl is None:
            return "unknown"
        if dl < 0:
            return "expired"
        if dl <= 90:
            return "expiring"
        return "ok"

    @property
    def warranty_label(self) -> str:
        """状态标签文案，如：保修剩 8 个月 / 保修剩 45 天 / 已过保

        剩余 90 天内切"天"（与 expiring 黄色阈值一致），
        避免出现"绿色标签写着剩 3 个月"的观感矛盾。
        """
        dl = self.days_left
        if dl is None:
            return "保修期待填写"
        if dl < 0:
            return "已过保"
        if dl <= 90:
            return f"保修剩 {dl} 天"
        months = dl // 30
        if months < 12:
            return f"保修剩 {months + 1} 个月"
        years = months / 12
        return f"保修剩 {round(years, 1) if years < 10 else round(years)} 年"

    @property
    def warranty_progress(self) -> int:
        """保修剩余比例（0-100），用于详情页进度条

        分母用真实总天数（到期日 - 购买日），不用"每月 30 天"近似——
        6 年保修按 30 天/月算偏差约 18%，进度条会明显失真。
        """
        dl = self.days_left
        if dl is None or self.purchase_date is None or not self.warranty_months:
            return 0
        total_days = (self.warranty_end - self.purchase_date).days
        if total_days <= 0:
            return 0
        return max(0, min(100, round(dl / total_days * 100)))

    # ---------- 保养任务关联 ----------

    tasks = relationship(
        "MaintenanceTask", back_populates="device", cascade="all, delete-orphan"
    )

    @property
    def next_task(self):
        """最近一次待保养的任务（按 next_date 最早的）"""
        pending = [t for t in self.tasks if t.next_date]
        return min(pending, key=lambda t: t.next_date) if pending else None

    @property
    def photo_url(self) -> str | None:
        """铭牌照片地址（建档时拍的那张）；没有照片返回 None"""
        return _device_photo_url(self.id) if self.id else None


class MaintenanceTask(Base):
    """保养任务：一台设备按品类模板自动生成，可多条"""

    __tablename__ = "maintenance_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    title = Column(String(100), nullable=False, comment="保养项目，如：清洗滤网")
    interval_months = Column(Integer, nullable=False, comment="周期（月）")
    next_date = Column(Date, nullable=False, comment="下次保养日期")
    last_done_at = Column(Date, comment="上次完成日期")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    device = relationship("Device", back_populates="tasks")

    @property
    def days_until(self) -> int:
        """距下次保养的天数，负数表示已逾期"""
        return (self.next_date - date.today()).days

    @property
    def due_label(self) -> str:
        """时间文案：已逾期 5 天 / 今天该保养 / 12 天后"""
        d = self.days_until
        if d < 0:
            return f"已逾期 {-d} 天"
        if d == 0:
            return "今天该保养"
        return f"{d} 天后"

    @property
    def is_overdue(self) -> bool:
        return self.days_until < 0
