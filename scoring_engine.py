try:
    from config import SELLER_CONSTRAINTS
    WEIGHTS = SELLER_CONSTRAINTS.get("weights", {})
except (ImportError, AttributeError):
    # 默认权重
    WEIGHTS = {
        "demand": 0.30,
        "profit": 0.30,
        "cross_border": 0.25,
        "competition": 0.15,
    }


def calculate_opportunity_score(
    demand: float,
    cross_border: float,
    profit: float,
    competition: float,
) -> float:
    """
    计算关键词的综合机会评分。

    评分公式（权重可从 config.py 配置）:
        机会分 = demand * w_demand + profit * w_profit
               + cross_border * w_cross_border - competition * w_competition

    参数:
        demand: 市场需求分数 (0-100)
        cross_border: 跨境友好度 (0-100)
        profit: 利润潜力 (0-100)
        competition: 竞争激烈度 (0-100)

    返回:
        综合评分 (0-100)
    """
    score = (
        demand * WEIGHTS.get("demand", 0.30)
        + profit * WEIGHTS.get("profit", 0.30)
        + cross_border * WEIGHTS.get("cross_border", 0.25)
        - competition * WEIGHTS.get("competition", 0.15)
    )

    return round(max(0, min(100, score)), 2)