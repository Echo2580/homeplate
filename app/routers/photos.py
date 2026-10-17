# 文件路径：app/routers/photos.py
# 铭牌照片上传接口：先存临时文件换 token，建档时再落盘（见 app/photos.py）
from fastapi import APIRouter, HTTPException, UploadFile

from app.photos import save_pending

router = APIRouter(prefix="/api", tags=["铭牌照片"])

# iPhone 相册默认 HEIC，浏览器/详情页都渲染不了，直接拒收并给出可操作的提示
HEIC_TYPES = ("image/heic", "image/heif")
HEIC_HINT = "iPhone 的 HEIC 照片暂不支持：请在「设置 → 相机 → 格式」选「兼容性最佳」，或把照片转成 JPG 后再试"

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB，与识别接口口径一致


@router.post("/photo", summary="上传铭牌照片，返回一次性 token（建档时带上）")
async def upload_photo(image: UploadFile):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    if image.content_type.lower() in HEIC_TYPES:
        raise HTTPException(status_code=400, detail=HEIC_HINT)
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片太大，请控制在 10MB 以内")

    token = save_pending(data, image.content_type)
    return {"ok": True, "token": token}
