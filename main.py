from tqdm import tqdm

from loader import load_excel
from feature_engine import calculate_market_features

from market_agent import analyze_keyword

from scoring_engine import calculate_opportunity_score
from ranking_engine import build_rankings

df = load_excel(
    "data/input.xlsx"
)

results=[]

for _,row in tqdm(df.iterrows(),total=len(df)):

    keyword=row["搜索查询"]

    features = calculate_market_features(row)

    ai = analyze_keyword(
        keyword,
        row
    )

    opportunity = calculate_opportunity_score(
        features["demand_score"],
        ai["cross_border_score"],
        ai["profit_score"],
        ai["competition_score"]
    )

    results.append({
        **row.to_dict(),
        **features,
        **ai,
        "opportunity_score":opportunity
    })

import pandas as pd

result_df = pd.DataFrame(results)

rankings = build_rankings(
    result_df
)

result_df.to_excel(
    "output/result.xlsx",
    index=False
)

print("完成")