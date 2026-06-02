def build_rankings(df):

    result={}

    result["TOP50"] = (
        df.sort_values(
            "opportunity_score",
            ascending=False
        )
        .head(50)
    )

    result["BLUE_OCEAN"] = (
        df.sort_values(
            "competition_score"
        )
        .head(20)
    )

    result["HIGH_PROFIT"] = (
        df.sort_values(
            "profit_score",
            ascending=False
        )
        .head(20)
    )

    return result