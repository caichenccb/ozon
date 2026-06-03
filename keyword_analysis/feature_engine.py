import pandas as pd


def calculate_market_features(row):
    """
    基于市场数据计算量化的市场特征分数。

    参数:
        row: pandas Series，包含市场数据列

    返回:
        dict: 包含各项市场特征分数
    """
    # --- 需求分 ---
    # 搜索热门度 40% + 加购率 30% + 转化率 30%
    demand_score = (
        _safe_get(row, "搜索查询热门度", 0) * 0.4
        + _safe_get(row, "加入购物车", 0) * 0.3
        + _safe_get(row, "订单转化率", 0) * 0.3
    )
    # 归一化到 0-100
    demand_score = _normalize_score(demand_score)

    # --- 价格竞争力分 ---
    # 基于商品价格判断是否在目标价格区间
    price = _safe_get(row, "商品价格", 0)
    if price >= 5000:
        price_score = 80
    elif price >= 3000:
        price_score = 60
    elif price >= 2000:
        price_score = 40
    elif price >= 1000:
        price_score = 20
    else:
        price_score = 0

        # --- 市场活跃度 ---
    # SPU 数量和卖家数量反映市场成熟度
    spu_count = _safe_get(row, "SPU数量", 0)
    seller_count = _safe_get(row, "卖家数量", 0)
    if spu_count > 0 and seller_count > 0:
        concentration = seller_count / max(spu_count, 1)
        if concentration < 1.5:
            market_activity_score = 30
        elif concentration < 3:
            market_activity_score = 50
        elif concentration < 5:
            market_activity_score = 70
        else:
            market_activity_score = 90
    else:
        market_activity_score = 50

    return {
        "demand_score": round(demand_score, 2),
        "price_score": price_score,
        "market_activity_score": market_activity_score,
    }


def _safe_get(row, column: str, default=0):
    """安全获取行中的列值"""
    try:
        val = row[column]
        if pd.isna(val):
            return default
        return val
    except (KeyError, TypeError):
        return default


def _normalize_score(value: float, max_value: float = 100) -> float:
    """将分数归一化到 0-100 范围"""
    return max(0, min(100, value))