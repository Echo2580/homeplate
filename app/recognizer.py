# 文件路径：app/recognizer.py
# 铭牌识别服务：调阿里百炼 Qwen-VL 多模态模型，从铭牌照片提取设备信息
import base64
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL = os.getenv("QWEN_VL_MODEL", "qwen-vl-plus")

PROMPT = """你是家电铭牌识别助手。图片中是家电设备的铭牌。
请识别铭牌上的信息，只返回一个 JSON 对象（不要 markdown 代码块，不要任何多余文字）：
{"brand": "品牌", "model_name": "型号", "serial_number": "序列号", "category": "品类"}
说明：
- category 必须从这些里选一个：空调、冰箱、洗衣机、净水器、电热水器、油烟机、电视、扫地机器人
- 看不清或铭牌上没有的字段填 null
"""


def recognize_nameplate(image_bytes: bytes) -> dict:
    """识别铭牌照片，返回 {brand, model_name, serial_number, category}；失败抛异常"""
    if not API_KEY or "填你的" in API_KEY:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，请在 .env 中填入阿里百炼的 API Key")

    client = OpenAI(
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    b64 = base64.b64encode(image_bytes).decode()
    data_uri = f"data:image/jpeg;base64,{b64}"

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
    )
    text = (resp.choices[0].message.content or "").strip()

    # 模型偶尔会在 JSON 外面包话或代码块，截取第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"模型没有返回 JSON：{text[:120]}")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败：{e}") from e

    # 只保留四个合法字段，多余的一律丢弃
    return {k: data.get(k) for k in ("brand", "model_name", "serial_number", "category")}
