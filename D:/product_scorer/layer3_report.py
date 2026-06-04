"""Layer 3: 标准输出报告层"""

import json
from pathlib import Path
from typing import Any
from .models import DecisionOutput, ProductInput, VisionOutput
from .config import OUTPUT_DIR

def format_score_bar(value: float, max_val: float, width: int = 20) -> str:
    filled = min(int((value / max_val) * width) if max_val > 0 else 0, width)
    return "█" * filled + "░" * (width - filled)

def print_report(result: DecisionOutput):
    s, v = result.scores, result.verdict
    total = s.total
    emoji = {"strong_hit": "🔥", "test_waters": "🧪", "cautious": "⚠️"}.get(s.grade(), "❌")
    ma, pp, ca, oz = result.market_analysis, result.product_positioning, result.competition_analysis, result.ozon_fit_analysis
    print(f"\n{'='*60}\n📋 Ozon 爆品评分报告\n{'='*60}")
    print(f"\n┌─ 1. 市场机会分析 ─────────────────────────┐\n  类目趋势：{ma.category_trend}\n  需求本质：{ma.demand_nature}\n  结构性机会：{ma.structural_opportunity}")
    print(f"\n│ 2. 产品定位分析\n│   目标人群：{pp.target_users}\n│   使用场景：{pp.use_scenarios}\n│   购买动机：{pp.buying_motivation}\n│   替代方案：{pp.alternatives}")
    print(f"\n│ 3. 竞争分析\n│   竞品打法：{ca.mainstream_tactics}\n│   同质化程度：{ca.homogenization_level}\n│   关键胜因：{ca.key_to_win}")
    print(f"\n│ 4. Ozon运营适配\n│   搜索关键词：{' | '.join(oz.search_keywords_ru[:5]) if oz.search_keywords_ru else 'N/A'}\n│   流量结构：{oz.traffic_structure}\n│   适合投广告：{'✅ 是' if oz.ad_suitable else '❌ 否'}")
    print(f"\n┌─ 5. 爆品评分（满分100） ────────────────────┐")
    for label, val, max_v in [("① 市场需求", s.market_demand, 25), ("② 利润空间", s.profit_margin, 25), ("③ 竞争难度", s.competition_ease, 20), ("④ 差异化能力", s.differentiation, 20), ("⑤ 转化潜力", s.conversion_potential, 10)]:
        print(f"│  {label}  {val:>5.1f}/{max_v:<3} {format_score_bar(val, max_v)} │")
    print(f"│  👉 总分：{total:>5.1f}/100  {emoji} {v.conclusion_cn}  │")
    print(f"\n┌─ 6. 最终商业判断 ─────────────────────────┐\n│  结论：{v.conclusion_cn}\n│  核心原因：{v.core_reason}\n│  是否放量：{v.scale_decision}")
    if ma.missing_info:
        print(f"\n⚠️  信息缺失项:")
        for item in ma.missing_info: print(f"   • {item}")

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
    with open(filepath, "w", encoding="utf-8") as f: json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📄 完整报告已导出: {filepath}")
    return str(filepath)
