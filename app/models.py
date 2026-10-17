# 文件路径：app/models.py
# 数据库表模型：设备档案（含保修状态计算）
import calendar
from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, Text, func

from app.database import Base


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
        """状态标签文案，如：保修剩 8 个月 / 保修剩 45 天 / 已过保"""
        dl = self.days_left
        if dl is None:
            return "保修期待填写"
        if dl < 0:
            return "已过保"
        if dl <= 90:
            return f"保修剩 {dl} 天"
        return f"保修剩 {max(1, round(dl / 30))} 个月"

    @property
    def warranty_progress(self) -> int:
        """保修剩余比例（0-100），用于详情页进度条"""
        dl = self.days_left
        if dl is None or not self.warranty_months:
            return 0
        total_days = self.warranty_months * 30
        return max(0, min(100, round(dl / total_days * 100)))
