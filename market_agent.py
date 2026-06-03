from openai import OpenAI
from dotenv import load_dotenv

import os
import json
import time

import pandas as pd

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 卖家约束（从 config.py 同步，避免循环依赖）
SELLER_PROFILE = """
- 中国跨境卖家，从中国直发
- 物流时效 15-30 天
- 不做低价商品（客单价 ≥ 2000 卢布）
- 不做高退货率品类
- 希望高利润率
- 希望低市场竞争
- 避免品类：服装、鞋子、电子零件、液体
"""


def analyze_keyword(keyword: str, row) -> dict:
    """
    调用 DeepSeek API 分析关键词的跨境选品机会。

    参数:
        keyword: 搜索关键词
        row: 该关键词对应的市场数据行（pandas Series）

    返回:
        dict: 包含评分和推荐的 JSON
    """
    # 将市场数据转为字典，并排除非数值/无关字段以提高 token 效率
    market_data = _prepare_market_data(row)

    prompt = f"""你是 Ozon 跨境选品专家。请基于以下卖家画像和市场数据，分析关键词的市场机会。

【卖家画像】
{SELLER_PROFILE}

【关键词】
{keyword}

【市场数据】
{json.dumps(market_data, ensure_ascii=False, indent=2)}

【分析要求】
请从以下维度进行评分（0-100 分）：
1. cross_border_score - 跨境友好度：该品类是否适合中国跨境卖家的物流和运营模式
2. profit_score - 利润潜力：考虑客单价、利润率空间、退货风险后的利润潜力
3. competition_score - 竞争激烈度：市场竞争程度，越高表示越激烈
4. logistics_risk - 物流风险：运输难度、破损率、时效要求
5. after_sales_risk - 售后风险：退货率、纠纷率、差评风险

【输出格式】
请严格输出 JSON 对象，不要包含其他内容：
{{
    "cross_border_score": 0,
    "profit_score": 0,
    "competition_score": 0,
    "logistics_risk": 0,
    "after_sales_risk": 0,
    "recommendation": "",
    "reason": ""
}}

评分说明：
- 所有评分范围 0-100
- cross_border_score、profit_score 越高越好
- competition_score、logistics_risk、after_sales_risk 越低越好
- recommendation：推荐建议（"强烈推荐" / "推荐" / "谨慎" / "不推荐"）
- reason：详细的分析理由"""

    max_retries = 3
    last_error = None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是Ozon跨境选品专家。请严格按用户要求的JSON格式输出分析结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                # 确保所有必要字段存在
                result.setdefault("cross_border_score", 50)
                result.setdefault("profit_score", 50)
                result.setdefault("competition_score", 50)
                result.setdefault("logistics_risk", 50)
                result.setdefault("after_sales_risk", 50)
                result.setdefault("recommendation", "")
                result.setdefault("reason", "")
                return result

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  ⏳ API 调用失败，{wait}秒后重试 ({attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                print(f"  ❌ API 调用失败 ({max_retries}次重试后放弃): {e}")

    # 所有重试失败，返回默认值
    return {
        "cross_border_score": 50,
        "profit_score": 50,
        "competition_score": 50,
        "logistics_risk": 50,
        "after_sales_risk": 50,
        "recommendation": "分析失败",
        "reason": f"DeepSeek API 调用失败: {last_error}",
    }


def _prepare_market_data(row) -> dict:
    """预处理市场数据，只保留关键字段"""
    important_keys = [
        "搜索查询", "搜索查询热门度", "加入购物车", "订单转化率",
        "商品价格", "SPU数量", "品牌数量", "卖家数量",
        "好评率", "评分", "类目",
    ]
    data = {}
    for key in important_keys:
        if key in row.index:
            try:
                val = row[key]
                if isinstance(val, float) and pd.isna(val):
                    val = None
                data[key] = val
            except Exception:
                data[key] = None
    return data