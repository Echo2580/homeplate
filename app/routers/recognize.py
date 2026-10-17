# 文件路径：app/routers/recognize.py
# 铭牌照片识别接口
import time

from fastapi import APIRouter, HTTPException, UploadFile

from app.recognizer import recognize_nameplate

router = APIRouter(prefix="/api", tags=["铭牌识别"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/recognize", summary="识别铭牌照片，返回结构化设备信息")
async def recognize(image: UploadFile):
    # 基本校验：必须是图片、不能为空、不能太大
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    data = await image.read()
    if not data:
        raise HTTPException(status_code=400, detail="图片内容为空")
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片太大，请控制在 10MB 以内")

    start = time.perf_counter()
    try:
        result = recognize_nameplate(data)
    except RuntimeError as e:
        # 配置缺失属于服务端环境问题
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ValueError as e:
        # 模型返回内容无法解析
        raise HTTPException(status_code=502, detail=f"识别结果解析失败：{e}") from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"识别服务调用失败：{e}") from e
    elapsed = round(time.perf_counter() - start, 1)

    # 只保留四个合法字段，多余的一律丢弃
    clean = {k: result.get(k) for k in ("brand", "model_name", "serial_number", "category")}
    return {"ok": True, "result": clean, "elapsed_seconds": elapsed}
