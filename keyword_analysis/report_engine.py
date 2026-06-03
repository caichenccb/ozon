import json
from pathlib import Path

import pandas as pd


def export_results(result_df: pd.DataFrame, rankings: dict) -> None:
    """
    导出分析结果到 Excel 和 JSON。

    - output/result.xlsx: 完整数据
    - output/rankings.xlsx: 多个排名榜单（每个榜单一个 sheet）
    - output/report.json: JSON 格式完整报告
    """
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 导出完整数据
    result_df.to_excel(
        output_dir / "result.xlsx",
        index=False,
        engine="openpyxl",
    )

    # 2. 导出分榜单 Excel（多 Sheet）
    with pd.ExcelWriter(
        output_dir / "rankings.xlsx",
        engine="openpyxl",
    ) as writer:
        # sheet 名称映射
        sheet_map = {
            "综合机会TOP50": "top50",
            "蓝海市场TOP20": "blue_ocean",
            "高利润TOP20": "high_profit",
            "高需求TOP20": "high_demand",
            "最适跨境TOP20": "best_cross_border",
        }

        for sheet_name, key in sheet_map.items():
            if key in rankings:
                df_sheet = rankings[key]
                if isinstance(df_sheet, pd.DataFrame) and not df_sheet.empty:
                    df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)

        # 写入概览 sheet
        if "summary" in rankings:
            summary_df = pd.DataFrame(
                [rankings["summary"]]
            ).T.reset_index()
            summary_df.columns = ["指标", "数值"]
            summary_df.to_excel(writer, sheet_name="数据概览", index=False)

    # 3. 导出 JSON 报告
    report = {
        "summary": rankings.get("summary", {}),
        "rankings": {},
    }

    for key in ["top50", "blue_ocean", "high_profit", "high_demand", "best_cross_border"]:
        if key in rankings and isinstance(rankings[key], pd.DataFrame):
            report["rankings"][key] = json.loads(
                rankings[key].to_json(orient="records", force_ascii=False)
            )

    with open(output_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def export_json(data: dict) -> None:
    """兼容旧接口：导出 JSON 报告（保留原有功能）"""
    export_results(
        result_df=pd.DataFrame(),
        rankings={"summary": data} if isinstance(data, dict) else {},
    )