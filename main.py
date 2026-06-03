import sys
import os
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
from tqdm import tqdm

load_dotenv()

# 检查 DeepSeek API Key
if not os.getenv("DEEPSEEK_API_KEY"):
    print("❌ 错误: 未找到 DEEPSEEK_API_KEY 环境变量")
    print("请创建 .env 文件并添加: DEEPSEEK_API_KEY=你的key")
    sys.exit(1)

from loader import load_excel
from feature_engine import calculate_market_features
from market_agent import analyze_keyword
from scoring_engine import calculate_opportunity_score
from ranking_engine import build_rankings
from report_engine import export_results


def main():
    # 确保输入文件存在
    input_path = "data/input.xlsx"
    if not Path(input_path).exists():
        print(f"❌ 错误: 未找到输入文件 {input_path}")
        print("请将 Ozon 关键词数据 Excel 文件放在 data/ 目录下，命名为 input.xlsx")
        return

    # 确保输出目录存在
    Path("output").mkdir(parents=True, exist_ok=True)

    print("📂 加载数据...")
    df = load_excel(input_path)
    print(f"✅ 共加载 {len(df)} 条关键词数据")

    # 校验必要列是否存在
    required_columns = ["搜索查询", "搜索查询热门度", "加入购物车", "订单转化率"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        print(f"❌ 数据缺少必要列: {missing}")
        return

    results = []

    print("🔍 开始分析关键词...")
    for _, row in tqdm(df.iterrows(), total=len(df), desc="分析进度"):
        keyword = row["搜索查询"]

        try:
            # 1. 基于市场数据的量化特征
            features = calculate_market_features(row)

            # 2. AI 分析（DeepSeek）
            ai = analyze_keyword(keyword, row)

            # 3. 综合机会评分
            opportunity = calculate_opportunity_score(
                demand=features["demand_score"],
                cross_border=ai.get("cross_border_score", 0),
                profit=ai.get("profit_score", 0),
                competition=ai.get("competition_score", 0),
            )

            results.append({
                **row.to_dict(),
                **features,
                **ai,
                "opportunity_score": opportunity,
            })

        except Exception as e:
            print(f"\n⚠️  关键词 '{keyword}' 分析失败: {e}")
            results.append({
                **row.to_dict(),
                "demand_score": 0,
                "cross_border_score": 0,
                "profit_score": 0,
                "competition_score": 0,
                "logistics_risk": 0,
                "after_sales_risk": 0,
                "recommendation": "",
                "reason": f"分析异常: {e}",
                "opportunity_score": 0,
            })

    result_df = pd.DataFrame(results)

    # 4. 构建排名榜单
    print("📊 生成排名榜单...")
    rankings = build_rankings(result_df)

    # 5. 导出结果
    export_results(result_df, rankings)

    print("\n✅ 全部完成！")
    print(f"📁 结果已保存至:")
    print(f"   - output/result.xlsx         (完整数据)")
    print(f"   - output/report.json         (JSON 报告)")
    print(f"   - output/rankings.xlsx       (分榜单)")


if __name__ == "__main__":
    main()