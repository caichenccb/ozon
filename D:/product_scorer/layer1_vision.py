"""Layer 1: 视觉识别层（Vision Prompt）"""

import base64, json
from pathlib import Path
from typing import Any
from openai import OpenAI
from .models import VisionOutput, ProductInput
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, OPENAI_API_KEY, OPENAI_VISION_MODEL, VISION_PROVIDER

_deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
_openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

LAYER1_VISION_SYSTEM_PROMPT = """\
你是一个产品视觉识别系统。请严格根据图片内容识别产品，并输出结构化JSON。
❗不要做商业分析，不要评价好坏，不要预测是否能卖。
❗只做"看图识别"。
必须输出以下JSON结构：
{
    "product_name": "", "category": "", "sub_category": "",
    "visual_features": {"shape": "", "color": "", "material_guess": "", "size_relation": ""},
    "components": [], "visible_functions": [], "usage_scene": "", "possible_users": [], "confidence": 0.0
}
规则：所有字段必须填写，不确定的用"未知"，不得编造，不得输出商业建议。"""

def load_image_base64(image_path: str) -> dict[str, Any] | None:
    if not image_path: return None
    path = Path(image_path)
    if not path.exists(): raise FileNotFoundError(f"图片文件未找到: {image_path}")
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:image/{path.suffix.lstrip('.')};base64,{encoded}"}}

def analyze_by_deepseek(product: ProductInput) -> dict[str, Any]:
    image_content = load_image_base64(product.image_path)
    if not image_content: return {}
    user_content: list[dict[str, Any]] = [{"type": "text", "text": f"请识别图中产品，严格按要求的JSON格式输出。\n用户提供参考信息（可选）：名称={product.name}, 类目={product.category}"}, image_content]
    response = _deepseek_client.chat.completions.create(
        model=DEEPSEEK_MODEL, messages=[{"role": "system", "content": LAYER1_VISION_SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
        temperature=0.1, response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content) if content else {}

def analyze_by_openai(product: ProductInput) -> dict[str, Any]:
    if not _openai_client: raise RuntimeError("OPENAI_API_KEY 未配置")
    image_content = load_image_base64(product.image_path)
    if not image_content: return {}
    user_content: list[dict[str, Any]] = [{"type": "text", "text": "请识别图中产品，严格按要求的JSON格式输出。"}, image_content]
    response = _openai_client.chat.completions.create(
        model=OPENAI_VISION_MODEL, messages=[{"role": "system", "content": LAYER1_VISION_SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
        temperature=0.1, response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content) if content else {}

def analyze_product_image(product: ProductInput) -> VisionOutput:
    print(f"\n{'='*60}\n📸 [Layer 1] 视觉识别层 — 解读产品图片...\n{'='*60}")
    if not product.image_path:
        print("  ⚠️  未提供图片，跳过视觉识别")
        return VisionOutput()
    raw = analyze_by_openai(product) if VISION_PROVIDER == "openai" else analyze_by_deepseek(product)
    if not raw:
        print("  ❌ 视觉识别返回空结果")
        return VisionOutput()
    result = VisionOutput.from_dict(raw)
    print(f"  ✅ 识别完成: {result.product_name} / {result.category} / 置信度{result.confidence:.0%}")
    return result

def merge_vision_to_input(vision: VisionOutput, product: ProductInput) -> ProductInput:
    if not product.name and vision.product_name: product.name = vision.product_name
    if not product.category and vision.category: product.category = vision.category
    if not product.material and vision.visual_features.material_guess: product.material = vision.visual_features.material_guess
    return product
