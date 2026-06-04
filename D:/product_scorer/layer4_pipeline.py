"""Layer 4: 系统拼接逻辑 — 完整链路编排"""

from typing import Any
from .models import ProductInput, VisionOutput, DecisionOutput
from .layer1_vision import analyze_product_image, merge_vision_to_input
from .layer2_decision import score_product
from .layer3_report import print_report, export_report

def run_full_pipeline(product: ProductInput, verbose: bool = True) -> dict[str, Any]:
    if verbose:
        print(f"\n{'#'*60}\n# 🚀 Ozon 产品爆品评分流水线\n# 产品: {product.name or '待识别'}\n# 图片: {product.image_path or '无'}\n{'#'*60}")
    vision = analyze_product_image(product)
    product = merge_vision_to_input(vision, product)
    if verbose and vision.product_name: print(f"\n  ✅ 产品已识别: {vision.product_name}")
    decision = score_product(vision, product)
    if verbose: print_report(decision)
    json_path = export_report(decision, vision, product)
    return {
        "layer_1_vision": vision.to_dict(),
        "layer_2_decision": decision.to_dict(),
        "layer_3_report_path": json_path,
        "summary": {"product_name": product.name or vision.product_name, "total_score": decision.scores.total, "grade": decision.scores.grade(), "grade_cn": decision.scores.grade_cn(), "conclusion": decision.verdict.conclusion, "conclusion_cn": decision.verdict.conclusion_cn},
    }
