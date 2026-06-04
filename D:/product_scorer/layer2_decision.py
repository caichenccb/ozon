"""Layer 2: Ozon 选品决策引擎（核心大脑）"""

import json
from typing import Any
from openai import OpenAI
from .models import ProductInput, VisionOutput, DecisionOutput
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

LAYER2_OZON_SYSTEM_PROMPT = """\
你是一位拥有15年以上经验的Ozon跨境电商产品总监，专注俄罗斯电商市场。
你的任务不是解释产品，而是做商业决策。

必须输出：
1. 市场机会分析
2. 产品定位分析
3. 竞争分析
4. Ozon运营适配分析
5. 100分爆品评分（市场需求0-25 利润空间0-25 竞争难度0-20 差异化能力0-20 转化潜力0-10）
6. 最终结论（recommended/test_waters/cautious/not_recommended）

【Ozon专用规则】优先考虑俄罗斯市场特性（价格敏感+物流成本+低客单接受度）
考虑Ozon佣金约15%、物流成本约350₽/kg、关税约5%
低客单价<500₽利润空间极窄，高退货率品类自动扣分
【防幻觉】信息不足标注"未知"，不得编造

必须输出严格JSON格式：
{
    "market_analysis": {"category_trend":"", "demand_nature":"", "structural_opportunity":"", "missing_info":[]},
    "product_positioning": {"target_users":"", "use_scenarios":"", "buying_motivation":"", "alternatives":""},
    "competition_analysis": {"mainstream_tactics":"", "homogenization_level":"", "entry_points":[], "key_to_win":""},
    "ozon_fit_analysis": {"search_keywords_ru":[], "traffic_structure":"", "conversion_strategy":"", "ad_suitable":true},
    "scores": {"market_demand":0, "profit_margin":0, "competition_ease":0, "differentiation":0, "conversion_potential":0, "total":0},
    "verdict": {"conclusion":"", "conclusion_cn":"", "core_reason":"", "scale_decision":""}
}"""

def score_product(vision: VisionOutput, product: ProductInput) -> DecisionOutput:
    print(f"\n{'='*60}\n🧠 [Layer 2] Ozon 选品决策引擎 — 正在分析...\n{'='*60}")
    input_json = {"vision_analysis": vision.to_dict(), "user_provided": {"name": product.name, "category": product.category, "dimensions": product.dimensions, "material": product.material, "price_rub": product.price_rub, "cost_rub": product.cost_rub, "weight_kg": product.weight_kg}}
    if product.price_rub > 0 and product.cost_rub > 0:
        commission = product.price_rub * 0.15
        logistics = max(product.weight_kg * 350, 200)
        duty = product.cost_rub * 0.05
        profit = product.price_rub - product.cost_rub - commission - logistics - duty
        margin = profit / product.price_rub * 100 if product.price_rub > 0 else 0
        input_json["profit_calculation"] = {"profit_rub": round(profit,1), "margin_percent": round(margin,1)}
        print(f"  💰 利润率预估: {margin:.1f}%")

    try:
        response = _client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "system", "content": LAYER2_OZON_SYSTEM_PROMPT},
                      {"role": "user", "content": f"请对以下产品进行 Ozon 选品判断：\n\n{json.dumps(input_json, ensure_ascii=False, indent=2)}"}],
            temperature=0.3, response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content: raise ValueError("API 返回空内容")
        raw = json.loads(content)
        result = DecisionOutput.from_dict(raw)
        if result.scores.total <= 0: result.scores.calculate_total()
        s = result.scores
        print(f"  ✅ 决策完成: {s.market_demand}/25 + {s.profit_margin}/25 + {s.competition_ease}/20 + {s.differentiation}/20 + {s.conversion_potential}/10 = {s.total}/100")
        print(f"  🏆 结论: {result.verdict.conclusion_cn}")
        return result
    except Exception as e:
        print(f"  ❌ 决策引擎调用失败: {e}")
        return DecisionOutput()
