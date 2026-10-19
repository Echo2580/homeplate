# 文件路径：app/schemas.py
# Pydantic 模型：定义接口的请求/响应数据格式
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# 长度上限与 models.py 的数据库列宽一致：超长在应用层拦截，
# 在应用层限制长度，保持数据库切换前后的输入约束一致。
NAME_MAX = 100
BRAND_MAX = 50
MODEL_MAX = 100
NOTES_MAX = 2000


class DeviceCreate(BaseModel):
    """创建设备：只要求 name 必填，其余选填"""

    name: str = Field(max_length=NAME_MAX)
    brand: str | None = Field(default=None, max_length=BRAND_MAX)
    model_name: str | None = Field(default=None, max_length=MODEL_MAX)
    serial_number: str | None = Field(default=None, max_length=MODEL_MAX)
    category: str | None = Field(default=None, max_length=50)
    purchase_date: date | None = None
    warranty_months: int | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX)
    # 铭牌照片 token：先调 POST /api/photo 上传拿到，建档成功后转正；不是数据库字段
    photo_token: str | None = None


class DeviceUpdate(BaseModel):
    """更新设备：全部选填，传了哪个字段就改哪个"""

    name: str | None = Field(default=None, max_length=NAME_MAX)
    brand: str | None = Field(default=None, max_length=BRAND_MAX)
    model_name: str | None = Field(default=None, max_length=MODEL_MAX)
    serial_number: str | None = Field(default=None, max_length=MODEL_MAX)
    category: str | None = Field(default=None, max_length=50)
    purchase_date: date | None = None
    warranty_months: int | None = None
    notes: str | None = Field(default=None, max_length=NOTES_MAX)


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
    # 仅建档接口会填：铭牌照片是否成功存档（非数据库字段，查询接口恒为 None）
    photo_saved: bool | None = None
