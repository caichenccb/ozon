def calculate_opportunity_score(
    demand,
    cross_border,
    profit,
    competition
):

    score = (
        demand * 0.30 +
        profit * 0.30 +
        cross_border * 0.25 -
        competition * 0.15
    )

    return round(score,2)