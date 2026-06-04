"""Layer 5: 系统工程优化层"""

import json, time
from typing import Any, Callable
from .models import DecisionOutput

def sanitize_json_response(raw_content: str) -> str:
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].strip().startswith("```"): lines = lines[1:]
        if lines and lines[-1].strip() == "```": lines = lines[:-1]
        content = "\n".join(lines)
    lines = [l for l in content.split("\n") if not l.strip().startswith("//") and not l.strip().startswith("#")]
    return "\n".join(lines).strip()

def parse_json_safe(content: str) -> dict[str, Any]:
    try: return json.loads(sanitize_json_response(content))
    except json.JSONDecodeError: return {}

SCORE_RANGES = {"market_demand": (0, 25), "profit_margin": (0, 25), "competition_ease": (0, 20), "differentiation": (0, 20), "conversion_potential": (0, 10)}

def validate_scores(scores: dict[str, float]) -> dict[str, float]:
    validated = {}
    for key, (min_v, max_v) in SCORE_RANGES.items():
        val = scores.get(key, 0)
        validated[key] = max(min_v, min(max_v, float(val) if isinstance(val, (int, float)) else 0))
    return validated

def validate_decision(result: DecisionOutput) -> DecisionOutput:
    result.scores.market_demand = max(0, min(25, result.scores.market_demand))
    result.scores.profit_margin = max(0, min(25, result.scores.profit_margin))
    result.scores.competition_ease = max(0, min(20, result.scores.competition_ease))
    result.scores.differentiation = max(0, min(20, result.scores.differentiation))
    result.scores.conversion_potential = max(0, min(10, result.scores.conversion_potential))
    result.scores.calculate_total()
    grade_to_conclusion = {"strong_hit": "recommended", "test_waters": "test_waters", "cautious": "cautious", "not_recommended": "not_recommended"}
    auto_grade = result.scores.grade()
    if auto_grade == "strong_hit" and result.verdict.conclusion in ("not_recommended", "cautious"):
        result.verdict.conclusion = grade_to_conclusion[auto_grade]
    cn_map = {"recommended": "推荐", "test_waters": "可试水", "cautious": "谨慎进入", "not_recommended": "不建议做"}
    result.verdict.conclusion_cn = cn_map.get(result.verdict.conclusion, "未知")
    return result

def with_retry(func: Callable, max_retries: int = 3, base_delay: float = 2.0, **kwargs) -> Any:
    last_error = None
    for attempt in range(max_retries):
        try: return func(**kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"  ⏳ 重试 ({attempt + 1}/{max_retries})，等待 {delay:.0f}s...")
                time.sleep(delay)
            else: print(f"  ❌ 已达最大重试次数 ({max_retries})，放弃")
    raise last_error

def calculate_ozon_profit(price_rub: float, cost_rub: float, weight_kg: float, commission_rate: float = 0.15, logistics_per_kg: float = 350, min_logistics: float = 200, duty_rate: float = 0.05) -> dict[str, float]:
    commission = price_rub * commission_rate
    logistics = max(weight_kg * logistics_per_kg, min_logistics)
    duty = cost_rub * duty_rate
    return_loss = price_rub * 0.08
    total_cost = cost_rub + commission + logistics + duty + return_loss
    profit = price_rub - total_cost
    margin = profit / price_rub if price_rub > 0 else 0
    return {"price_rub": round(price_rub, 1), "cost_rub": round(cost_rub, 1), "commission_rub": round(commission, 1), "logistics_rub": round(logistics, 1), "duty_rub": round(duty, 1), "return_loss_rub": round(return_loss, 1), "total_cost_rub": round(total_cost, 1), "profit_rub": round(profit, 1), "margin_percent": round(margin * 100, 1)}
