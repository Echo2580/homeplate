# 文件路径：app/schemas.py
# Pydantic 模型：定义接口的请求/响应数据格式
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    """创建设备：只要求 name 必填，其余选填"""

    name: str
    brand: str | None = None
    model_name: str | None = None
    serial_number: str | None = None
    category: str | None = None
    purchase_date: date | None = None
    warranty_months: int | None = None
    notes: str | None = None


class DeviceUpdate(BaseModel):
    """更新设备：全部选填，传了哪个字段就改哪个"""

    name: str | None = None
    brand: str | None = None
    model_name: str | None = None
    serial_number: str | None = None
    category: str | None = None
    purchase_date: date | None = None
    warranty_months: int | None = None
    notes: str | None = None


class DeviceOut(BaseModel):
    """返回给前端的设备信息"""

    id: int
    name: str
    brand: str | None
    model_name: str | None
    serial_number: str | None
    category: str | None
    purchase_date: date | None
    warranty_months: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # 允许直接从 SQLAlchemy 对象转换（Device -> DeviceOut）
    model_config = ConfigDict(from_attributes=True)
