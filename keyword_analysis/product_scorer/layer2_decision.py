"""
Layer 2: Ozon 选品决策引擎（核心大脑）
========================================
🎯 作用：判断能不能做、能不能赚钱、是否爆品、是否进入
🧠 使用：DeepSeek V4 Pro
📊 输出：标准 DecisionOutput JSON
"""

import json
from typing import Any

from openai import OpenAI

from .models import (
    ProductInput,
    VisionOutput,
    DecisionOutput,
    Scores,
)
from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)


# ══════════════════════════════════════════════
# Layer 2: Ozon 决策引擎 System Prompt
# ══════════════════════════════════════════════

LAYER2_OZON_SYSTEM_PROMPT = """\
你是一位拥有15年以上经验的Ozon跨境电商产品总监，专注俄罗斯电商市场。
你的任务不是解释产品，而是做商业决策。

你将收到一个结构化产品JSON，请进行Ozon选品判断。

【你的核心目标】
判断该产品是否适合在Ozon销售，并最大化利润机会。

必须输出：
1. 市场机会分析
2. 产品定位分析
3. 竞争分析
4. Ozon运营适配分析
5. 100分爆品评分
6. 最终结论（推荐 / 可试水 / 不建议）

【评分系统】
- 市场需求 0-25分
- 利润空间 0-25分
- 竞争难度 0-20分（越容易做分越高）
- 差异化能力 0-20分
- 转化潜力 0-10分

【Ozon专用规则】
- 必须优先考虑俄罗斯市场特性（价格敏感 + 物流成本 + 低客单接受度）
- 必须考虑：Ozon佣金约15%、物流成本约350₽/kg、关税约5%
- 低客单价（<500₽）利润空间极窄，谨慎评分
- 高退货率品类（服装、鞋类）自动扣分

【防幻觉规则】
- 如果信息不足，请明确标注"未知"，不得编造
- 如果无法从图片或输入中确定某字段，写"信息不足"
- 不确定的评分项按中位数给分并标注

【输出格式 - 严格JSON】
{
    "market_analysis": {
        "category_trend": "增长/饱和/下滑（带简要理由）",
        "demand_nature": "功能/情绪/刚需",
        "structural_opportunity": "是否存在结构性机会",
        "missing_info": ["缺失项1", "缺失项2"]
    },
    "product_positioning": {
        "target_users": "俄罗斯本地目标用户",
        "use_scenarios": "具体使用场景",
        "buying_motivation": "核心购买动机",
        "alternatives": "用户当前替代方案"
    },
    "competition_analysis": {
        "mainstream_tactics": "竞品主流打法",
        "homogenization_level": "高/中/低",
        "entry_points": ["空白点1", "空白点2"],
        "key_to_win": "赢的关键因素"
    },
    "ozon_fit_analysis": {
        "search_keywords_ru": ["俄语搜索关键词1", "俄语搜索关键词2"],
        "traffic_structure": "搜索为主/推荐为主/活动驱动",
        "conversion_strategy": "转化优化策略描述",
        "ad_suitable": true
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
        "conclusion": "recommended/test_waters/cautious/not_recommended",
        "conclusion_cn": "推荐/可试水/谨慎进入/不建议做",
        "core_reason": "一句话核心原因",
        "scale_decision": "是/小规模测试后决定/否"
    }
}
"""


# ══════════════════════════════════════════════
# 核心函数
# ══════════════════════════════════════════════

def _calculate_profit_margin(price_rub: float, cost_rub: float, weight_kg: float) -> dict[str, Any]:
    """
    计算利润空间，辅助评分参考。
    """
    commission = price_rub * 0.15
    logistics = max(weight_kg * 350, 200)
    duty = cost_rub * 0.05 if cost_rub > 0 else 0
    total_cost = cost_rub + commission + logistics + duty
    profit = price_rub - total_cost
    margin_rate = profit / price_rub if price_rub > 0 else 0

    return {
        "price_rub": price_rub,
        "cost_rub": cost_rub,
        "commission_rub": round(commission, 1),
        "logistics_rub": round(logistics, 1),
        "duty_rub": round(duty, 1),
        "total_cost_rub": round(total_cost, 1),
        "profit_rub": round(profit, 1),
        "margin_rate": round(margin_rate * 100, 1),
    }


def score_product(
    vision: VisionOutput,
    product: ProductInput,
) -> DecisionOutput:
    """
    Layer 2 主入口：用 DeepSeek V4 Pro 进行 Ozon 选品决策。

    参数:
        vision: Layer 1 视觉识别结果
        product: 用户输入

    返回:
        DecisionOutput: 完整的决策结果
    """
    print(f"\n{'='*60}")
    print(f"🧠 [Layer 2] Ozon 选品决策引擎 — 正在分析...")
    print(f"{'='*60}")

    # 构建输入产品 JSON
    input_json = {
        "vision_analysis": vision.to_dict(),
        "user_provided": {
            "name": product.name,
            "category": product.category,
            "dimensions": product.dimensions,
            "material": product.material,
            "price_rub": product.price_rub,
            "cost_rub": product.cost_rub,
            "weight_kg": product.weight_kg,
        },
    }

    # 如果提供了价格和成本，加上利润计算参考
    if product.price_rub > 0 and product.cost_rub > 0:
        profit_calc = _calculate_profit_margin(
            product.price_rub, product.cost_rub, product.weight_kg
        )
        input_json["profit_calculation"] = profit_calc
        print(f"  💰 利润预估: 售价={profit_calc['price_rub']}₽, "
              f"成本={profit_calc['cost_rub']}₽, "
              f"利润率={profit_calc['margin_rate']}%")

    try:
        response = _client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": LAYER2_OZON_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "请对以下产品进行 Ozon 选品判断：\n\n"
                        f"{json.dumps(input_json, ensure_ascii=False, indent=2)}"
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("API 返回空内容")

        raw = json.loads(content)
        result = DecisionOutput.from_dict(raw)

        # 确保总分计算
        if result.scores.total <= 0:
            result.scores.calculate_total()

        # 打印摘要
        s = result.scores
        print(f"  ✅ 决策完成")
        print(f"  📊 评分: {s.market_demand}/25 + {s.profit_margin}/25 + "
              f"{s.competition_ease}/20 + {s.differentiation}/20 + "
              f"{s.conversion_potential}/10 = {s.total}/100")
        print(f"  🏆 结论: {result.verdict.conclusion_cn}")
        print(f"  💡 原因: {result.verdict.core_reason}")

        return result

    except Exception as e:
        print(f"  ❌ 决策引擎调用失败: {e}")
        return DecisionOutput()
