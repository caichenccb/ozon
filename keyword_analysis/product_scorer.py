"""
产品爆品评分器 — 图片解读 + Ozon产品总监Skill评分

流程：
  1. 用户上传产品图片 → 用 DeepSeek V4 Pro 视觉能力解读图片（产品识别、属性提取）
  2. 将解读结果 + 用户补充信息 → 喂给 Ozon产品总监 Skill 评分框架
  3. 输出 100 分制爆品评分 + 最终商业判断

用法：
  python product_scorer.py --image path/to/product.jpg
  python product_scorer.py --image path/to/product.jpg --name "产品名" --category "类目"
  python product_scorer.py --url https://example.com/product.jpg  (暂不支持)
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ──────────────────────────────────────────────
# Client 初始化
# ──────────────────────────────────────────────

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v4",
)


# ──────────────────────────────────────────────
# 数据模型
# ──────────────────────────────────────────────

@dataclass
class ProductImageInput:
    """产品图片输入"""
    name: str = ""
    category: str = ""
    image_path: str = ""
    dimensions: str = ""
    material: str = ""
    price_rub: float = 0.0
    cost_rub: float = 0.0  # 成本（含采购+物流）
    weight_kg: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)


def load_image_base64(image_path: str) -> dict[str, Any] | None:
    """加载图片为 base64，用于 vision API"""
    if not image_path:
        return None

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"图片文件未找到: {image_path}")

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/{path.suffix.lstrip('.')};base64,{encoded}"},
    }


# ──────────────────────────────────────────────
# 第1步：图片解读 Agent — 用视觉能力识别产品
# ──────────────────────────────────────────────

IMAGE_ANALYSIS_SYSTEM_PROMPT = """
你是 Ozon 跨境电商的产品分析师。你擅长通过产品图片识别以下信息：

请严格输出 JSON，包含以下字段：
{
    "product_name_cn": "产品中文名称（简洁）",
    "product_name_en": "产品英文名称",
    "category": "产品类目（如：家居装饰、厨房用品、电子配件、户外用品等）",
    "sub_category": "细分类目",
    "materials": ["材质1", "材质2"],
    "estimated_dimensions_cm": "估算尺寸（如 15x10x5 cm）",
    "estimated_weight_kg": 0.0,
    "colors": ["颜色1", "颜色2"],
    "features": ["功能/特征1", "功能/特征2"],
    "target_users_ru": "俄罗斯目标用户描述",
    "use_scenarios_ru": "俄罗斯使用场景描述",
    "quality_impression": "low/medium/high（材质做工印象）",
    "ozon_price_estimate_rub": 0,
    "visual_description": "图片的视觉描述，包括产品外观、包装、背景、风格"
}

注意：
- 所有识别结果基于图片视觉信息 + 你的电商知识推断
- 如果某字段无法从图片判断，设为 null
- category 和 name 必须尽量准确
"""


def analyze_product_image(product: ProductImageInput) -> dict[str, Any]:
    """
    通过 DeepSeek V4 Pro 视觉能力解读产品图片，
    提取产品属性信息。
    """
    print(f"\n{'='*60}")
    print(f"📸 [Step 1] 正在解读产品图片...")
    print(f"{'='*60}")

    image_content = load_image_base64(product.image_path)
    if not image_content:
        print("  ⚠️  未提供图片，跳过视觉分析")
        return {}

    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "请分析这张产品图片，识别产品信息。\n"
                f"用户提供的额外信息：\n"
                f"  名称: {product.name or '未知'}\n"
                f"  类目: {product.category or '未知'}\n"
                f"  尺寸: {product.dimensions or '未知'}\n"
                f"  材质: {product.material or '未知'}\n"
            ),
        },
        image_content,
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": IMAGE_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            print(f"  ✅ 图片解读完成")
            print(f"  📦 产品: {result.get('product_name_cn', '?')} | {result.get('product_name_en', '?')}")
            print(f"  🏷️  类目: {result.get('category', '?')} > {result.get('sub_category', '?')}")
            print(f"  🎨 材质: {', '.join(result.get('materials', ['?']))}")
            print(f"  📐 估算尺寸: {result.get('estimated_dimensions_cm', '?')}")
            print(f"  💰 预估Ozon售价: {result.get('ozon_price_estimate_rub', '?')} ₽")
            return result
    except Exception as e:
        print(f"  ❌ 图片解读失败: {e}")

    return {}


# ──────────────────────────────────────────────
# 第2步：Ozon产品总监 Skill 评分
# ──────────────────────────────────────────────

OZON_DIRECTOR_SYSTEM_PROMPT = """
你是 Ozon 跨境电商产品总监，拥有 15 年跨境电商经验，专注于俄罗斯 Ozon 平台。
你的核心职责不是提供建议，而是作为"选品与商业决策系统"，对产品进行可量化评估与淘汰判断。

你的评分体系如下：

## 评分维度（满分100分）
1. 市场需求强度 (0-25分)：是否刚需？是否高频？是否有增长趋势？
2. 利润空间 (0-25分)：成本 vs 售价空间；运费与佣金压缩后是否仍有利润；是否具备规模化利润？
3. 竞争难度 (0-20分)：是否红海？是否同质化严重？是否容易被价格战碾压？（越容易做 → 分数越高）
4. 差异化能力 (0-20分)：是否可以做出明显区别？是否能靠设计/功能/组合突围？
5. Ozon转化潜力 (0-10分)：标题搜索匹配度；图片/详情页表达能力；是否适合平台推荐逻辑？

## 总分判断规则
- 80-100分：🔥 强爆品（优先做，全力投入）
- 60-79分：🧪 可试水（小规模测试，验证后放量）
- 40-59分：⚠️ 谨慎进入（除非有特殊优势，否则不入）
- 0-39分：❌ 不建议做（直接放弃）

## 工作规则
1. 不允许模糊表达 — 必须可决策
2. 不允许只分析不打分 — 必须给出量化评分
3. 必须以"赚钱能力"为核心标准
4. 必须站在 Ozon 真实运营逻辑（俄罗斯物流、关税、退货率、佣金结构）
5. 信息不足必须指出缺失项
6. 所有结论必须可用于执行决策

## 输出格式 - 严格 JSON
{
    "market_analysis": {
        "category_trend": "增长/饱和/下滑",
        "demand_nature": "功能/情绪/刚需",
        "structural_opportunity": "描述结构性机会",
        "missing_info": ["缺失信息列表"]
    },
    "product_positioning": {
        "target_users": "俄罗斯目标用户描述",
        "use_scenarios": "具体使用场景",
        "buying_motivation": "核心购买动机",
        "alternatives": "用户当前的替代方案"
    },
    "competition_analysis": {
        "mainstream_tactics": "竞品主流打法",
        "homogenization_level": "高/中/低",
        "entry_points": ["可切入的空白点"],
        "key_to_win": "赢的关键因素"
    },
    "ozon_fit_analysis": {
        "search_keywords_ru": ["俄语搜索关键词"],
        "traffic_structure": "搜索/推荐/活动",
        "conversion_strategy": "转化优化策略",
        "ad_suitable": true,
        "expected_commission_rub": 0,
        "expected_logistics_rub": 0
    },
    "scores": {
        "market_demand": 0,
        "profit_margin": 0,
        "competition_ease": 0,
        "differentiation": 0,
        "conversion_potential": 0,
        "total": 0
    },
    "verdict": {
        "conclusion": "recommended|test_waters|cautious|not_recommended",
        "conclusion_cn": "推荐|可试水|谨慎进入|不建议做",
        "core_reason": "一句话核心原因",
        "scale_decision": "是/小规模测试后决定/否"
    }
}
"""


def score_product(image_analysis: dict[str, Any], product: ProductImageInput) -> dict[str, Any]:
    """
    调用 DeepSeek V4 Pro，以 Ozon产品总监 Skill 的评分框架对产品进行爆品评分。
    """
    print(f"\n{'='*60}")
    print(f"📊 [Step 2] Ozon产品总监 爆品评分中...")
    print(f"{'='*60}")

    # 构建输入
    product_info = {
        "user_provided": {
            "name": product.name,
            "category": product.category,
            "dimensions": product.dimensions,
            "material": product.material,
            "price_rub": product.price_rub,
            "cost_rub": product.cost_rub,
            "weight_kg": product.weight_kg,
        },
        "image_analysis": image_analysis,
    }

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": OZON_DIRECTOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请用 Ozon 跨境电商产品总监的评分框架，对以下产品进行爆品评分。\n\n"
                        f"产品信息：\n{json.dumps(product_info, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            print(f"  ✅ 评分完成！")
            return result

    except Exception as e:
        print(f"  ❌ 评分调用失败: {e}")

    return {}


# ──────────────────────────────────────────────
# 第3步：可视化报告输出
# ──────────────────────────────────────────────

def print_score_report(result: dict[str, Any]):
    """将评分结果格式化为终端输出"""
    scores = result.get("scores", {})
    verdict = result.get("verdict", {})

    print(f"\n{'='*60}")
    print(f"📋 爆品评分报告")
    print(f"{'='*60}")

    # 评分表
    total = scores.get("total", 0)
    print(f"""
┌──────────────────────────────────────┐
│         📊 爆品评分（{total}/100）           │
├──────────────────────────────────────┤
│ ① 市场需求强度     {scores.get('market_demand', 0):>3}/{25}                          │
│ ② 利润空间         {scores.get('profit_margin', 0):>3}/{25}                          │
│ ③ 竞争难度         {scores.get('competition_ease', 0):>3}/{20}                          │
│ ④ 差异化能力       {scores.get('differentiation', 0):>3}/{20}                          │
│ ⑤ Ozon转化潜力     {scores.get('conversion_potential', 0):>3}/{10}                          │
├──────────────────────────────────────┤""")

    # 结论
    conclusion = verdict.get("conclusion_cn", "未知")
    emoji_map = {"推荐": "🔥", "可试水": "🧪", "谨慎进入": "⚠️", "不建议做": "❌"}
    emoji = emoji_map.get(conclusion, "❓")

    print(f"│ 👉 总分：{total}/100  {emoji} {conclusion}                   │")
    print(f"└──────────────────────────────────────┘")

    # 核心原因
    print(f"\n💡 核心判断：{verdict.get('core_reason', 'N/A')}")
    print(f"📈 是否放量：{verdict.get('scale_decision', 'N/A')}")

    # 市场分析摘要
    market = result.get("market_analysis", {})
    print(f"""
📌 市场机会
   - 类目趋势：{market.get('category_trend', 'N/A')}
   - 需求本质：{market.get('demand_nature', 'N/A')}
   - 结构性机会：{market.get('structural_opportunity', 'N/A')}""")

    # 竞争分析
    comp = result.get("competition_analysis", {})
    print(f"""
📌 竞争分析
   - 竞品打法：{comp.get('mainstream_tactics', 'N/A')}
   - 同质化程度：{comp.get('homogenization_level', 'N/A')}
   - 关键胜因：{comp.get('key_to_win', 'N/A')}""")

    # Ozon运营适配
    ozon = result.get("ozon_fit_analysis", {})
    keywords = ozon.get("search_keywords_ru", [])
    print(f"""
📌 Ozon运营适配
   - 搜索关键词：{' | '.join(keywords[:5]) if keywords else 'N/A'}
   - 适合投广告：{'✅ 是' if ozon.get('ad_suitable') else '❌ 否'}
   - 转化策略：{ozon.get('conversion_strategy', 'N/A')}""")

    # 缺失信息
    missing = market.get("missing_info", [])
    if missing:
        print(f"\n⚠️  信息缺失项（影响评分准确性）:")
        for item in missing:
            print(f"   - {item}")


def export_json_report(result: dict[str, Any], analysis: dict[str, Any],
                       product: ProductImageInput, output_dir: str = "output") -> str:
    """将完整报告导出为 JSON 文件"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report = {
        "product_input": asdict(product),
        "image_analysis": analysis,
        "score_result": result,
    }

    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_"
                        for ch in (product.name or "product")).strip("_")
    filepath = output_path / f"{safe_name}_scoring_report.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 完整报告已保存: {filepath}")
    return str(filepath)


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def run_pipeline(product: ProductImageInput) -> dict[str, Any]:
    """
    运行完整流程：
    1. 图片解读（如果有图片）
    2. Ozon产品总监 Skill 评分
    3. 输出报告
    """
    # Step 1: 图片解读
    image_analysis = analyze_product_image(product) if product.image_path else {}

    # 补充：如果图片分析有值而用户没填，自动补全
    if image_analysis:
        if not product.name and image_analysis.get("product_name_cn"):
            product.name = image_analysis["product_name_cn"]
        if not product.category and image_analysis.get("category"):
            product.category = image_analysis["category"]
        if not product.dimensions and image_analysis.get("estimated_dimensions_cm"):
            product.dimensions = image_analysis["estimated_dimensions_cm"]
        if not product.material and image_analysis.get("materials"):
            product.material = ", ".join(image_analysis["materials"])

    # Step 2: 评分
    result = score_product(image_analysis, product)

    # Step 3: 输出
    print_score_report(result)
    export_json_report(result, image_analysis, product)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Ozon 产品爆品评分器 — 上传图片 + AI解读 + 产品总监Skill评分"
    )
    parser.add_argument("--image", "-i", type=str, default="",
                        help="产品图片路径")
    parser.add_argument("--name", "-n", type=str, default="",
                        help="产品名称（可选，如不传会从图片识别）")
    parser.add_argument("--category", "-c", type=str, default="",
                        help="产品类目（可选）")
    parser.add_argument("--price", "-p", type=float, default=0.0,
                        help="Ozon 售价（卢布）")
    parser.add_argument("--cost", type=float, default=0.0,
                        help="产品成本（含采购+物流，卢布）")
    parser.add_argument("--weight", "-w", type=float, default=0.0,
                        help="产品重量（kg）")
    parser.add_argument("--dimensions", "-d", type=str, default="",
                        help="产品尺寸（如 15x10x5 cm）")
    parser.add_argument("--material", "-m", type=str, default="",
                        help="产品材质")

    args = parser.parse_args()

    # 如果没有参数，进入交互模式
    if len(sys.argv) == 1:
        print("=" * 60)
        print("🚀 Ozon 产品爆品评分器")
        print("=" * 60)

        image_path = input("\n📸 产品图片路径（留空跳过）: ").strip().strip('"').strip("'")
        name = input("📦 产品名称（留空自动识别）: ").strip()
        category = input("🏷️  产品类目（留空自动识别）: ").strip()
        price_str = input("💵 Ozon 售价（卢布，留空跳过）: ").strip()
        cost_str = input("💰 产品成本（卢布，含采购+物流，留空跳过）: ").strip()
        weight_str = input("⚖️  产品重量（kg，留空跳过）: ").strip()
        dimensions = input("📐 产品尺寸（如 15x10x5 cm，留空跳过）: ").strip()
        material = input("🧪 产品材质（留空自动识别）: ").strip()

        product = ProductImageInput(
            name=name,
            category=category,
            image_path=image_path,
            price_rub=float(price_str) if price_str else 0.0,
            cost_rub=float(cost_str) if cost_str else 0.0,
            weight_kg=float(weight_str) if weight_str else 0.0,
            dimensions=dimensions,
            material=material,
        )
    else:
        product = ProductImageInput(
            name=args.name,
            category=args.category,
            image_path=args.image,
            price_rub=args.price,
            cost_rub=args.cost,
            weight_kg=args.weight,
            dimensions=args.dimensions,
            material=args.material,
        )

    run_pipeline(product)


if __name__ == "__main__":
    # 需要 base64 编码图片
    import base64
    main()
