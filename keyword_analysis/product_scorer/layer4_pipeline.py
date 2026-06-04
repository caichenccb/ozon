"""
Layer 4: 系统拼接逻辑（最关键）
================================
🔄 完整链路编排：

  用户上传图片
      ↓
  Layer 1: Vision Prompt（GPT-4o / DeepSeek V4 Pro Vision）
      ↓ 输出结构化 JSON
  Layer 2: Ozon 选品决策引擎（DeepSeek V4 Pro）
      ↓
  Layer 3: 标准输出报告
      ↓
  Layer 5: 工程优化注入
"""

from typing import Any

from .models import ProductInput, VisionOutput, DecisionOutput
from .layer1_vision import analyze_product_image, merge_vision_to_input
from .layer2_decision import score_product
from .layer3_report import print_report, export_report


def run_full_pipeline(
    product: ProductInput,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    运行完整 5 层流水线。

    参数:
        product: 产品输入（含图片路径、价格信息等）
        verbose: 是否打印详细信息

    返回:
        dict: 包含所有层输出的完整结果
    """
    # ════════════════════════════════════════
    # Layer 1: 视觉识别
    # ════════════════════════════════════════
    if verbose:
        print(f"\n{'#'*60}")
        print(f"# 🚀 Ozon 产品爆品评分流水线")
        print(f"# {'='*56}")
        print(f"# 产品: {product.name or '待识别'}")
        print(f"# 图片: {product.image_path or '无'}")
        print(f"{'#'*60}")

    vision = analyze_product_image(product)
    product = merge_vision_to_input(vision, product)

    if verbose and vision.product_name:
        print(f"\n  ✅ 产品已识别: {vision.product_name}")

    # ════════════════════════════════════════
    # Layer 2: Ozon 决策引擎
    # ════════════════════════════════════════
    decision = score_product(vision, product)

    # ════════════════════════════════════════
    # Layer 3: 标准报告
    # ════════════════════════════════════════
    if verbose:
        print_report(decision)

    json_path = export_report(decision, vision, product)

    return {
        "layer_1_vision": vision.to_dict(),
        "layer_2_decision": decision.to_dict(),
        "layer_3_report_path": json_path,
        "summary": {
            "product_name": product.name or vision.product_name,
            "total_score": decision.scores.total,
            "grade": decision.scores.grade(),
            "grade_cn": decision.scores.grade_cn(),
            "conclusion": decision.verdict.conclusion,
            "conclusion_cn": decision.verdict.conclusion_cn,
        },
    }
