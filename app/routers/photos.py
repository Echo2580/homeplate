# 文件路径：app/routers/photos.py
# 铭牌照片上传接口：先存临时文件换 token，建档时再落盘（见 app/photos.py）
from fastapi import APIRouter, HTTPException, UploadFile

from app.photos import save_pending

router = APIRouter(prefix="/api", tags=["铭牌照片"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB，与识别接口口径一致


@router.post("/photo", summary="上传铭牌照片，返回一次性 token（建档时带上）")
async def upload_photo(image: UploadFile):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片太大，请控制在 10MB 以内")

    token = save_pending(data, image.content_type)
    return {"ok": True, "token": token}
