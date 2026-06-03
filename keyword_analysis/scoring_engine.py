"""
评分引擎 - 批处理优化版

核心变更：
  1. 数值计算全部向量化（DataFrame 级别），不再逐行 iterrows()
  2. 新增 batch_compute_market_features(df) 一次算出所有市场特征
  3. 新增 batch_compute_opportunity_scores(df, ai_df) 一次算出所有机会分

  主流程变为：
    market_features = batch_compute_market_features(df)          # 纯向量化，毫秒级
    ai_results = batch_analyze_keywords(df)                      # 1 次 API 调用
    final_df = batch_compute_opportunity_scores(market_features, ai_results)  # 纯向量化
"""

import pandas as pd
import numpy as np

try:
    from config import SELLER_CONSTRAINTS
    WEIGHTS = SELLER_CONSTRAINTS.get("weights", {})
except (ImportError, AttributeError):
    WEIGHTS = {
        "demand": 0.30,
        "profit": 0.30,
        "cross_border": 0.25,
        "competition": 0.15,
    }

# ============================================================
# 批处理 API（推荐使用）
# ============================================================


def batch_compute_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    向量化计算所有关键词的市场特征分数。

    参数:
        df: 原始市场数据 DataFrame（必须含搜索查询热门度/加入购物车/订单转化率等列）

    返回:
        包含 demand_score, price_score, market_activity_score 的 DataFrame
    """
    result = pd.DataFrame(index=df.index)

    # --- 需求分 ---
    hot = _safe_col(df, "搜索查询热门度", 0)
    cart = _safe_col(df, "加入购物车", 0)
    conv = _safe_col(df, "订单转化率", 0)
    demand_score = hot * 0.4 + cart * 0.3 + conv * 0.3
    result["demand_score"] = demand_score.clip(0, 100).round(2)

    # --- 价格竞争力分 ---
    price = _safe_col(df, "商品价格", 0)
    price_score = pd.cut(
        price,
        bins=[-1, 1000, 2000, 3000, 5000, float("inf")],
        labels=[0, 20, 40, 60, 80],
    ).astype(int)
    result["price_score"] = price_score

    # --- 市场活跃度 ---
    spu = _safe_col(df, "SPU数量", 0)
    seller = _safe_col(df, "卖家数量", 0)
    # 避免除零
    concentration = seller / spu.replace(0, 1)
    conditions = [
        (spu <= 0) | (seller <= 0),
        concentration < 1.5,
        concentration < 3,
        concentration < 5,
        ]
    choices = [50, 30, 50, 70]
    result["market_activity_score"] = pd.Series(
        data=np.select(conditions, choices, default=90),
        index=df.index,
    )

    return result


def batch_compute_opportunity_scores(
    market_df: pd.DataFrame,
    ai_df: pd.DataFrame,
) -> pd.Series:
    """
    向量化计算所有关键词的综合机会评分。

    参数:
        market_df: batch_compute_market_features 的输出
        ai_df: batch_analyze_keywords 的输出（或等结构的 DataFrame）

    返回:
        机会评分 Series（0-100）
    """
    w_demand = WEIGHTS.get("demand", 0.30)
    w_profit = WEIGHTS.get("profit", 0.30)
    w_cross = WEIGHTS.get("cross_border", 0.25)
    w_compet = WEIGHTS.get("competition", 0.15)

    score = (
        market_df["demand_score"] * w_demand
        + ai_df.get("profit_score", 0) * w_profit
        + ai_df.get("cross_border_score", 0) * w_cross
        - ai_df.get("competition_score", 0) * w_compet
    )
    return score.clip(0, 100).round(2)


# ============================================================
# 逐行 API（保留向后兼容）
# ============================================================


def calculate_market_features(row) -> dict:
    """
    （逐行版）基于市场数据计算量化的市场特征分数。

    参数:
        row: pandas Series，包含市场数据列

    返回:
        dict: 包含各项市场特征分数
    """
    demand_score = (
        _safe_get(row, "搜索查询热门度", 0) * 0.4
        + _safe_get(row, "加入购物车", 0) * 0.3
        + _safe_get(row, "订单转化率", 0) * 0.3
    )
    demand_score = _normalize_score(demand_score)

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


def calculate_opportunity_score(
    demand: float,
    cross_border: float,
    profit: float,
    competition: float,
) -> float:
    """
    （逐行版）计算关键词的综合机会评分。

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


def compute_full_score(row_data: dict, ai_result: dict) -> dict:
    """
    （逐行版）一站式完成：市场特征计算 + AI结果整合 + 机会评分

    参数:
        row_data: 原始市场数据行 (dict 或 pandas Series)
        ai_result: AI 分析结果 (dict)

    返回:
        dict: 包含所有特征和评分的完整结果
    """
    features = calculate_market_features(row_data)
    opportunity = calculate_opportunity_score(
        demand=features["demand_score"],
        cross_border=ai_result.get("cross_border_score", 0),
        profit=ai_result.get("profit_score", 0),
        competition=ai_result.get("competition_score", 0),
    )
    return {
        **features,
        **ai_result,
        "opportunity_score": opportunity,
    }


# ============================================================
# 内部工具函数
# ============================================================


def _safe_col(df: pd.DataFrame, column: str, default=0):
    """DataFrame 级别安全取值"""
    if column in df.columns:
        return df[column].fillna(default)
    return pd.Series(default, index=df.index)


def _safe_get(row, column: str, default=0):
    """逐行安全获取列值"""
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
