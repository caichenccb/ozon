"""
Layer 5: 系统工程优化层
=======================
🔥 工程优化要点：

  1. 强制 JSON（防乱输出）— Vision 模型只能输出 JSON，不能写长文本
  2. 防幻觉规则 — 信息不足标注"未知"，不得编造
  3. Ozon 专用强化点 — 俄罗斯市场特性自动化注入
  4. 利润预估计算器 — 自动推算毛利润
  5. 评分校验器 — 确保评分在合理范围内
  6. 重试与容错 — API 调用失败自动重试
"""

import json
import time
from typing import Any, Callable

from .models import Scores, DecisionOutput


# ══════════════════════════════════════════════
# 1. JSON 净化器（防模型乱输出）
# ══════════════════════════════════════════════

def sanitize_json_response(raw_content: str) -> str:
    """
    从模型响应中提取纯净 JSON。
    处理模型可能在 JSON 前后添加注释、markdown 标记等。
    """
    content = raw_content.strip()

    # 去掉 ```json ... ``` 包裹
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    # 去掉可能的注释行（// 或 # 开头的行）
    lines = content.split("\n")
    lines = [l for l in lines if not l.strip().startswith("//") and not l.strip().startswith("#")]
    content = "\n".join(lines)

    return content.strip()


def parse_json_safe(content: str) -> dict[str, Any]:
    """安全解析 JSON，失败时返回空字典"""
    try:
        cleaned = sanitize_json_response(content)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


# ══════════════════════════════════════════════
# 2. 评分校验器（确保分数在合理范围）
# ══════════════════════════════════════════════

SCORE_RANGES = {
    "market_demand": (0, 25),
    "profit_margin": (0, 25),
    "competition_ease": (0, 20),
    "differentiation": (0, 20),
    "conversion_potential": (0, 10),
}


def validate_scores(scores: dict[str, float]) -> dict[str, float]:
    """校验并修正评分范围"""
    validated = {}
    for key, (min_v, max_v) in SCORE_RANGES.items():
        val = scores.get(key, 0)
        if not isinstance(val, (int, float)):
            val = 0
        validated[key] = max(min_v, min(max_v, float(val)))
    return validated


def validate_decision(result: DecisionOutput) -> DecisionOutput:
    """校验完整的决策输出"""
    # 校验评分
    result.scores.market_demand = max(0, min(25, result.scores.market_demand))
    result.scores.profit_margin = max(0, min(25, result.scores.profit_margin))
    result.scores.competition_ease = max(0, min(20, result.scores.competition_ease))
    result.scores.differentiation = max(0, min(20, result.scores.differentiation))
    result.scores.conversion_potential = max(0, min(10, result.scores.conversion_potential))
    result.scores.calculate_total()

    # 校验结论与评分一致性
    auto_grade = result.scores.grade()
    manual_conclusion = result.verdict.conclusion

    # 如果手动结论与评分等级严重不符，按评分修正
    grade_to_conclusion = {
        "strong_hit": "recommended",
        "test_waters": "test_waters",
        "cautious": "cautious",
        "not_recommended": "not_recommended",
    }
    expected = grade_to_conclusion.get(auto_grade, "cautious")

    # 只有跨档位时才修正（例如总评 85 但不推荐）
    if auto_grade == "strong_hit" and manual_conclusion in ("not_recommended", "cautious"):
        result.verdict.conclusion = expected

    cn_map = {
        "recommended": "推荐",
        "test_waters": "可试水",
        "cautious": "谨慎进入",
        "not_recommended": "不建议做",
    }
    result.verdict.conclusion_cn = cn_map.get(result.verdict.conclusion, "未知")

    return result


# ══════════════════════════════════════════════
# 3. 重试机制
# ══════════════════════════════════════════════

def with_retry(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0,
    **kwargs,
) -> Any:
    """
    带指数退避的 API 调用重试包装器。

    用法:
        result = with_retry(my_api_call, model="xxx", messages=[...])
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            return func(**kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"  ⏳ 重试 ({attempt + 1}/{max_retries})，等待 {delay:.0f}s...")
                time.sleep(delay)
            else:
                print(f"  ❌ 已达最大重试次数 ({max_retries})，放弃")

    raise last_error


# ══════════════════════════════════════════════
# 4. Ozon 利润计算强化
# ══════════════════════════════════════════════

def calculate_ozon_profit(
    price_rub: float,
    cost_rub: float,
    weight_kg: float,
    commission_rate: float = 0.15,
    logistics_per_kg: float = 350,
    min_logistics: float = 200,
    duty_rate: float = 0.05,
) -> dict[str, float]:
    """
    Ozon 真实利润计算器。

    考虑因素:
    - Ozon 佣金 ~15%
    - 物流费 ~350₽/kg（最低 200₽）
    - 俄罗斯进口关税 ~5%
    - 退货损失 ~8%（预留）

    返回:
        dict: 各项费用和最终利润
    """
    commission = price_rub * commission_rate
    logistics = max(weight_kg * logistics_per_kg, min_logistics)
    duty = cost_rub * duty_rate
    return_loss = price_rub * 0.08  # 退货预留
    total_cost = cost_rub + commission + logistics + duty + return_loss
    profit = price_rub - total_cost
    margin = profit / price_rub if price_rub > 0 else 0

    return {
        "price_rub": round(price_rub, 1),
        "cost_rub": round(cost_rub, 1),
        "commission_rub": round(commission, 1),
        "logistics_rub": round(logistics, 1),
        "duty_rub": round(duty, 1),
        "return_loss_rub": round(return_loss, 1),
        "total_cost_rub": round(total_cost, 1),
        "profit_rub": round(profit, 1),
        "margin_percent": round(margin * 100, 1),
    }
