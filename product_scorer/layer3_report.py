"""
Layer 3: 标准输出报告层
=======================
🎯 作用：将决策结果格式化为可读报告
✅ 终端可视化 + JSON 导出（强制统一格式）
"""

import json
from pathlib import Path
from typing import Any

from .models import DecisionOutput, ProductInput, VisionOutput
from .config import OUTPUT_DIR


def format_score_bar(value: float, max_val: float, width: int = 20) -> str:
    filled = int((value / max_val) * width) if max_val > 0 else 0
    filled = min(filled, width)
    bar = "█" * filled + "░" * (width - filled)
    return bar


def print_report(result: DecisionOutput):
    s = result.scores
    v = result.verdict
    total = s.total
    conclusion_emoji = ""
    if total >= 80:      conclusion_emoji = "🔥"
    elif total >= 60:    conclusion_emoji = "🧪"
    elif total >= 40:    conclusion_emoji = "⚠️"
    else:                conclusion_emoji = "❌"

    print(f"\n{'='*60}")
    print(f"📋 Ozon 爆品评分报告")
    print(f"{'='*60}")
    ma = result.market_analysis
    print(f"""
┌─ 1. 市场机会分析 ─────────────────────────┐
  类目趋势：{ma.category_trend}
  需求本质：{ma.demand_nature}
  结构性机会：{ma.structural_opportunity}
├─────────────────────────────────────────────┤""")
    pp = result.product_positioning
    print(f"""
│ 2. 产品定位分析
│   目标人群：{pp.target_users}
│   使用场景：{pp.use_scenarios}
│   购买动机：{pp.buying_motivation}
│   替代方案：{pp.alternatives}
├─────────────────────────────────────────────┤""")
    ca = result.competition_analysis
    print(f"""
│ 3. 竞争分析
│   竞品打法：{ca.mainstream_tactics}
│   同质化程度：{ca.homogenization_level}
│   可切入空白点：{' | '.join(ca.entry_points[:3]) if ca.entry_points else 'N/A'}
│   关键胜因：{ca.key_to_win}
├─────────────────────────────────────────────┤""")
    oz = result.ozon_fit_analysis
    print(f"""
│ 4. Ozon运营适配
│   搜索关键词：{' | '.join(oz.search_keywords_ru[:5]) if oz.search_keywords_ru else 'N/A'}
│   流量结构：{oz.traffic_structure}
│   转化策略：{oz.conversion_strategy}
│   适合投广告：{'✅ 是' if oz.ad_suitable else '❌ 否'}
└─────────────────────────────────────────────┘""")
    print(f"""
┌─ 5. 爆品评分（满分100） ────────────────────┐""")
    items = [("① 市场需求", s.market_demand, 25), ("② 利润空间", s.profit_margin, 25), ("③ 竞争难度", s.competition_ease, 20), ("④ 差异化能力", s.differentiation, 20), ("⑤ 转化潜力", s.conversion_potential, 10)]
    for label, val, max_v in items:
        bar = format_score_bar(val, max_v)
        print(f"│  {label}  {val:>5.1f}/{max_v:<3} {bar} │")
    print(f"│                                             │")
    print(f"│  👉 总分：{total:>5.1f}/100  {conclusion_emoji} {v.conclusion_cn:<8}  │")
    print(f"└─────────────────────────────────────────────┘")
    print(f"""
┌─ 6. 最终商业判断 ─────────────────────────┐
│  结论：{v.conclusion_cn}
│  核心原因：{v.core_reason}
│  是否放量：{v.scale_decision}
└─────────────────────────────────────────────┘""")
    if ma.missing_info:
        print(f"\n⚠️  信息缺失项:")
        for item in ma.missing_info:
            print(f"   • {item}")


def export_report(result: DecisionOutput, vision: VisionOutput, product: ProductInput, output_dir: str | Path = None) -> str:
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "pipeline_version": "2.0",
        "layer_1_vision": {"provider": "deepseek-v4-pro", "output": vision.to_dict()},
        "layer_2_decision": {"model": "deepseek-v4-pro", "output": result.to_dict()},
        "layer_3_report": {"summary": {"total_score": result.scores.total, "grade": result.scores.grade(), "grade_cn": result.scores.grade_cn(), "conclusion": result.verdict.conclusion, "conclusion_cn": result.verdict.conclusion_cn}},
        "user_input": {"name": product.name, "category": product.category, "image_path": product.image_path, "dimensions": product.dimensions, "material": product.material, "price_rub": product.price_rub, "cost_rub": product.cost_rub, "weight_kg": product.weight_kg},
    }
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in (product.name or "product")).strip("_") or "product"
    filepath = output_dir / f"{safe_name}_ozon_report.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 完整报告已导出: {filepath}")
    return str(filepath)
