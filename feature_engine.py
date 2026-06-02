def calculate_market_features(row):

    demand_score = (
        row["搜索查询热门度"] * 0.4 +
        row["加入购物车"] * 0.3 +
        row["订单转化率"] * 0.3
    )

    return {
        "demand_score": demand_score
    }