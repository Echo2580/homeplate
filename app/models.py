# 文件路径：app/models.py
# 数据库表模型：设备档案
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.database import Base


class Device(Base):
    """家电设备档案表：一台设备一条记录"""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="设备名称，如：客厅空调")
    brand = Column(String(50), comment="品牌，如：格力")
    model_name = Column(String(100), comment="型号，如：KFR-35GW")
    serial_number = Column(String(100), comment="序列号（铭牌上识别）")
    category = Column(String(50), comment="品类：空调/冰箱/洗衣机/净水器...")
    purchase_date = Column(String(20), comment="购买日期，格式 YYYY-MM-DD")
    warranty_months = Column(Integer, comment="保修期（月），按品类默认值可改")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
