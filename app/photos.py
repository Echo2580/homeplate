# 文件路径：app/photos.py
# 铭牌照片存档：拍摄页先把照片存进临时目录换 token，建档成功后再转正为 device_{id}
# 设计说明：不新增数据库列——照片按设备 ID 命名，模型 property 直接查文件，免去迁移
import re
import secrets
import time
from pathlib import Path

# 项目根目录（app/ 的上一级）；静态目录用相对路径挂载，这里用绝对路径更稳
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
PENDING_DIR = UPLOAD_DIR / "_pending"

# 只接受这几种常见图片格式（前端压缩后统一是 JPEG）
EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
ALL_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")
PENDING_MAX_AGE_SECONDS = 24 * 60 * 60  # 拍了但没建档的临时照片保留 24 小时


def _ensure_dirs() -> None:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)


def save_pending(data: bytes, content_type: str | None) -> str:
    """把铭牌照片存进临时目录，返回一次性 token（32 位十六进制）"""
    _ensure_dirs()
    ext = EXT_BY_CONTENT_TYPE.get((content_type or "").lower(), ".jpg")
    token = secrets.token_hex(16)
    (PENDING_DIR / f"{token}{ext}").write_bytes(data)
    return token


def _pending_file(token: str | None) -> Path | None:
    """按 token 找临时照片；token 格式不对按无效处理，防止路径穿越"""
    if not token or not TOKEN_RE.match(token):
        return None
    if not PENDING_DIR.exists():
        return None
    for p in PENDING_DIR.glob(token + ".*"):
        if p.suffix.lower() in ALL_EXTENSIONS:
            return p
    return None


def finalize_pending(token: str | None, device_id: int) -> bool:
    """建档成功后把临时照片转正为 static/uploads/device_{id}{ext}"""
    src = _pending_file(token)
    if src is None:
        return False
    _ensure_dirs()
    remove_photo(device_id)  # 同一台设备只留一张，兜底
    dst = UPLOAD_DIR / f"device_{int(device_id)}{src.suffix.lower()}"
    src.replace(dst)  # 同盘移动，原子操作
    return True


def photo_path(device_id: int) -> Path | None:
    """按设备 ID 找已存档的铭牌照片；没有返回 None"""
    if not UPLOAD_DIR.exists():
        return None
    for ext in ALL_EXTENSIONS:
        p = UPLOAD_DIR / f"device_{int(device_id)}{ext}"
        if p.exists():
            return p
    return None


def photo_url(device_id: int) -> str | None:
    """详情页展示用的 URL；没有照片返回 None"""
    p = photo_path(device_id)
    return f"/static/uploads/{p.name}" if p else None


def remove_photo(device_id: int) -> bool:
    """删除设备时清理照片，避免孤儿文件"""
    p = photo_path(device_id)
    if p is None:
        return False
    p.unlink(missing_ok=True)
    return True


def cleanup_pending(max_age_seconds: int = PENDING_MAX_AGE_SECONDS) -> int:
    """服务启动时清理超期的临时照片（用户拍了但最终没保存的那些）"""
    if not PENDING_DIR.exists():
        return 0
    removed = 0
    deadline = time.time() - max_age_seconds
    for p in PENDING_DIR.iterdir():
        try:
            if p.is_file() and p.stat().st_mtime < deadline:
                p.unlink()
                removed += 1
        except OSError:
            continue
    return removed
