from openai import OpenAI
from dotenv import load_dotenv

import os
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def analyze_keyword(keyword,row):

    prompt=f"""
你是Ozon跨境选品专家。

卖家条件：

- 中国跨境卖家
- 物流15-30天
- 不做低客单
- 不做高退货
- 希望高利润
- 希望低竞争

关键词：

{keyword}

市场数据：

{row.to_dict()}

输出JSON：

{{
"cross_border_score":0,
"profit_score":0,
"competition_score":0,
"logistics_risk":0,
"after_sales_risk":0,
"recommendation":"",
"reason":""
}}
"""

    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role":"system",
                "content":"你是Ozon跨境选品专家"
            },
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0.2,
        response_format={
            "type":"json_object"
        },
        reasoning_effort="high",
        extra_body={
            "thinking":{
                "type":"enabled"
            }
        }
    )

    return json.loads(
        response.choices[0].message.content or ""
    )