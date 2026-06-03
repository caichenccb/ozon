def build_rankings(df):
    """
    构建多个维度的关键词排名榜单。

    参数:
        df: 包含所有关键词分析结果的 DataFrame

    返回:
        dict: 包含以下榜单:
            - top50: 综合机会分 TOP50
            - blue_ocean: 蓝海市场（竞争低 + 需求高）
            - high_profit: 高利润潜力 TOP20
            - high_demand: 高需求 TOP20
            - best_cross_border: 最适跨境 TOP20
            - summary: 数据概览
    """
    result = {}

    # 1. 综合机会 TOP50
    result["top50"] = (
        df.sort_values("opportunity_score", ascending=False)
        .head(50)
        .reset_index(drop=True)
    )

    # 2. 蓝海市场：低竞争 + 高需求
    df["blue_ocean_score"] = (
        df.get("demand_score", 0) * 0.6
        - df.get("competition_score", 0) * 0.4
    )
    result["blue_ocean"] = (
        df.sort_values("blue_ocean_score", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # 3. 高利润 TOP20
    result["high_profit"] = (
        df.sort_values("profit_score", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # 4. 高需求 TOP20
    result["high_demand"] = (
        df.sort_values("demand_score", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # 5. 最适跨境 TOP20
    result["best_cross_border"] = (
        df.sort_values("cross_border_score", ascending=False)
        .head(20)
        .reset_index(drop=True)
    )

    # 6. 数据概览
    result["summary"] = {
        "total_keywords": len(df),
        "avg_opportunity_score": round(df["opportunity_score"].mean(), 2),
        "avg_demand_score": round(df.get("demand_score", 0).mean(), 2),
        "avg_profit_score": round(df.get("profit_score", 0).mean(), 2),
        "avg_competition_score": round(df.get("competition_score", 0).mean(), 2),
        "avg_cross_border_score": round(df.get("cross_border_score", 0).mean(), 2),
        "top_keyword": df.loc[df["opportunity_score"].idxmax(), "搜索查询"]
            if "搜索查询" in df.columns else "",
        "top_score": round(df["opportunity_score"].max(), 2),
    }

    return result