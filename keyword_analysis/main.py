import sys
import os
from pathlib import Path
from dotenv import load_dotenv

import pandas as pd

load_dotenv()

# 检查 DeepSeek API Key
if not os.getenv("DEEPSEEK_API_KEY"):
    print("[错误] 未找到 DEEPSEEK_API_KEY 环境变量")
    print("请创建 .env 文件并添加: DEEPSEEK_API_KEY=你的key")
    sys.exit(1)

from loader import load_excel
from market_agent import batch_analyze_keywords
from scoring_engine import batch_compute_market_features, batch_compute_opportunity_scores
from ranking_engine import build_rankings
from report_engine import export_results


def main():
    # 确保输入文件存在
    input_path = "data/input.xlsx"
    if not Path(input_path).exists():
        print(f"[错误] 未找到输入文件 {input_path}")
        print("请将 Ozon 关键词数据 Excel 文件放在 data/ 目录下，命名为 input.xlsx")
        return

    # 确保输出目录存在
    Path("output").mkdir(parents=True, exist_ok=True)

    print("[1/5] 加载数据...")
    df = load_excel(input_path)
    print(f"  -> 共加载 {len(df)} 条关键词数据")

    # 校验必要列是否存在
    required_columns = ["搜索查询", "搜索查询热门度", "加入购物车", "订单转化率"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        print(f"[错误] 数据缺少必要列: {missing}")
        return

    # ============================================================
    # 第一步：批量计算市场特征（纯向量化运算，毫秒级完成）
    # ============================================================
    print("[2/5] 批量计算市场特征...")
    market_features = batch_compute_market_features(df)
    print(f"  -> 市场特征计算完成（{len(market_features)} 条）")
    print(f"  -> demand_score 范围: {market_features['demand_score'].min():.1f} - {market_features['demand_score'].max():.1f}")

    # ============================================================
    # 第二步：批量 AI 分析（所有关键词打包成 1 次 DeepSeek API 调用）
    # ============================================================
    print("[3/5] 批量 AI 分析（DeepSeek）...")
    ai_results = batch_analyze_keywords(df)
    print(f"  -> AI 分析完成（{len(ai_results)} 条）")

    # 检查是否有分析失败的
    failed = ai_results[ai_results["recommendation"] == "分析失败"]
    if not failed.empty:
        print(f"  ⚠️  有 {len(failed)} 条关键词分析失败，已使用默认值")

    # ============================================================
    # 第三步：统一计算机会评分（纯向量化运算）
    # ============================================================
    print("[4/5] 计算综合机会评分...")
    opportunity_scores = batch_compute_opportunity_scores(market_features, ai_results)
    print(f"  -> 机会评分完成")
    print(f"  -> opportunity_score 范围: {opportunity_scores.min():.1f} - {opportunity_scores.max():.1f}")

    # 组装最终 DataFrame
    result_df = pd.concat([
        df,
        market_features,
        ai_results,
        opportunity_scores.rename("opportunity_score"),
    ], axis=1)

    # ============================================================
    # 第四步：构建排名并导出
    # ============================================================
    print("[5/5] 生成排名榜单并导出结果...")
    rankings = build_rankings(result_df)
    export_results(result_df, rankings)

    print("\n全部完成！")
    print(f"结果已保存至 output/ 目录:")
    print(f"  - result.xlsx    (完整数据)")
    print(f"  - report.json    (JSON 报告)")
    print(f"  - rankings.xlsx  (分榜单)")


if __name__ == "__main__":
    main()
