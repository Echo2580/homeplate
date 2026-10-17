# 文件路径：app/recognizer.py
# 铭牌识别服务：调 OpenAI 兼容的多模态模型（DeepSeek / 百炼 Qwen-VL / 智谱均可），
# 从铭牌照片提取设备信息。供应商通过 .env 的三个变量切换，代码不用改。
import base64
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

try:
    import httpx2 as httpx_mod  # 新版 openai SDK 依赖 httpx2
except ImportError:
    import httpx as httpx_mod  # 旧版 openai SDK 依赖 httpx

load_dotenv()

API_BASE = os.getenv("AI_API_BASE")       # 如 https://api.deepseek.com
API_KEY = os.getenv("AI_API_KEY")         # 对应供应商的 API Key
MODEL = os.getenv("VISION_MODEL", "deepseek-flash")  # 如 deepseek-flash / qwen-vl-plus

PROMPT = """你是家电铭牌识别助手。图片中是家电设备的铭牌。
请识别铭牌上的信息，只返回一个 JSON 对象（不要 markdown 代码块，不要任何多余文字）：
{"name": "设备名称", "brand": "品牌", "model_name": "型号", "serial_number": "序列号", "category": "品类"}
说明：
- name：给这台设备起个家里的叫法，格式参考"品牌+品类"（如"格力空调"、"美的电压力锅"）；铭牌上有能区分位置/规格的信息就用上（如"海尔冰箱（厨房）"），没有就只写品牌+品类，不要编造
- category 必须从这些里选一个：空调、冰箱、洗衣机、净水器、电热水器、油烟机、电视、扫地机器人、电磁炉、微波炉、电饭煲、电风扇、电压力锅、热水壶、加湿器、空气净化器、取暖器、挂烫机、豆浆机、破壁机、其他、电压力锅、热水壶、加湿器、空气净化器、取暖器、挂烫机、豆浆机、破壁机、其他
- 看不清或铭牌上没有的字段填 null
"""


def recognize_nameplate(image_bytes: bytes) -> dict:
    """识别铭牌照片，返回 {brand, model_name, serial_number, category}；失败抛异常"""
    if not API_BASE or not API_KEY or "填你的" in API_KEY:
        raise RuntimeError(
            "识别模型未配置。请在 .env 中填写 AI_API_BASE、AI_API_KEY、VISION_MODEL 三个变量"
        )

    # trust_env=False：绕过系统代理环境变量——DeepSeek/百炼都是国内直连服务，
    # 走 Clash 代理会绕到国外节点再回来，识别耗时成倍增长
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE,
        http_client=httpx_mod.Client(trust_env=False, timeout=60.0),
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

    # 只保留五个合法字段，多余的一律丢弃
    return {k: data.get(k) for k in ("name", "brand", "model_name", "serial_number", "category")}
