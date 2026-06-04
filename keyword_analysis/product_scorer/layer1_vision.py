"""
Layer 1: 视觉识别层（Vision Prompt）
======================================
🎯 作用：把图片"翻译成标准产品 JSON"
❗ 核心原则：只描述，不做商业判断，不提 Ozon、不提利润
✅ 输出：标准化的 VisionOutput JSON
"""

import base64
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from .models import VisionOutput, ProductInput
from .config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    OPENAI_API_KEY,
    OPENAI_VISION_MODEL,
    VISION_PROVIDER,
)

# ──────────────────────────────────────────────
# Clients
# ──────────────────────────────────────────────

_deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)

_openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
) if OPENAI_API_KEY else None


# ══════════════════════════════════════════════
# Layer 1: Vision Prompt（工业级）
# ══════════════════════════════════════════════

LAYER1_VISION_SYSTEM_PROMPT = """\
你是一个产品视觉识别系统。
请严格根据图片内容识别产品，并输出结构化JSON。
❗不要做商业分析，不要评价好坏，不要预测是否能卖。
❗只做"看图识别"。

必须输出以下JSON结构：
{
    "product_name": "",
    "category": "",
    "sub_category": "",
    "visual_features": {
        "shape": "",
        "color": "",
        "material_guess": "",
        "size_relation": ""
    },
    "components": [],
    "visible_functions": [],
    "usage_scene": "",
    "possible_users": [],
    "confidence": 0.0
}

规则：
- product_name：产品中文名称，简洁准确
- category：一级类目（如：宠物用品、厨房用具、电子配件）
- sub_category：细分类目（如：智能宠物设备、烘焙工具）
- visual_features.shape：产品形状描述
- visual_features.color：主色调
- visual_features.material_guess：材质推断
- visual_features.size_relation：尺寸关系（如：手掌大小/中大型设备/便携式）
- components：从图片中可见的组成部分列表
- visible_functions：从图片中可见的功能/特征列表
- usage_scene：推测的使用场景
- possible_users：可能的用户群体
- confidence：识别置信度 0.0-1.0

⚠️ 注意：
- 所有字段必须填写，不能确认为空字符串
- 不得编造信息，不确定的用"未知"
- 不得输出任何商业建议
- 不得提及Ozon、销售、利润等商业词汇
"""


# ══════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════

def load_image_base64(image_path: str) -> dict[str, Any] | None:
    """加载图片为 base64"""
    if not image_path:
        return None
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件未找到: {image_path}")
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:image/{path.suffix.lstrip('.')};base64,{encoded}",
        },
    }


# ══════════════════════════════════════════════
# 核心函数
# ══════════════════════════════════════════════

def analyze_by_deepseek(product: ProductInput) -> dict[str, Any]:
    """用 DeepSeek V4 Pro Vision 做视觉识别"""
    image_content = load_image_base64(product.image_path)
    if not image_content:
        return {}

    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "请识别图中产品，严格按要求的JSON格式输出。\n"
                f"用户提供参考信息（可选）：名称={product.name}, 类目={product.category}"
            ),
        },
        image_content,
    ]

    response = _deepseek_client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": LAYER1_VISION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,  # 低温：严格识别，不要创意
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content) if content else {}


def analyze_by_openai(product: ProductInput) -> dict[str, Any]:
    """用 GPT-4o Vision 做视觉识别（更稳定）"""
    if not _openai_client:
        raise RuntimeError("OPENAI_API_KEY 未配置，无法使用 GPT-4o Vision")

    image_content = load_image_base64(product.image_path)
    if not image_content:
        return {}

    user_content: list[dict[str, Any]] = [
        {"type": "text", "text": "请识别图中产品，严格按要求的JSON格式输出。"},
        image_content,
    ]

    response = _openai_client.chat.completions.create(
        model=OPENAI_VISION_MODEL,
        messages=[
            {"role": "system", "content": LAYER1_VISION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    return json.loads(content) if content else {}


def analyze_product_image(product: ProductInput) -> VisionOutput:
    """
    Layer 1 主入口：识别产品图片 → 输出标准 VisionOutput

    根据配置选择用 GPT-4o 还是 DeepSeek V4 Pro。
    """
    print(f"\n{'='*60}")
    print(f"📸 [Layer 1] 视觉识别层 — 解读产品图片...")
    print(f"{'='*60}")

    if not product.image_path:
        print("  ⚠️  未提供图片，跳过视觉识别")
        return VisionOutput()

    if VISION_PROVIDER == "openai":
        print(f"  🔗 使用 GPT-4o Vision（OpenAI）")
        raw = analyze_by_openai(product)
    else:
        print(f"  🔗 使用 DeepSeek V4 Pro Vision")
        raw = analyze_by_deepseek(product)

    if not raw:
        print("  ❌ 视觉识别返回空结果")
        return VisionOutput()

    result = VisionOutput.from_dict(raw)
    print(f"  ✅ 识别完成")
    print(f"  📦 产品: {result.product_name}")
    print(f"  🏷️  类目: {result.category} > {result.sub_category}")
    print(f"  🎨 外形: {result.visual_features.shape} / {result.visual_features.color}")
    print(f"  🔬 置信度: {result.confidence:.0%}")
    return result


def merge_vision_to_input(vision: VisionOutput, product: ProductInput) -> ProductInput:
    """
    将视觉识别结果合并到用户输入。
    用户未提供的字段用识别结果补充。
    """
    if not product.name and vision.product_name:
        product.name = vision.product_name
    if not product.category and vision.category:
        product.category = vision.category
    if not product.material and vision.visual_features.material_guess:
        product.material = vision.visual_features.material_guess
    return product
