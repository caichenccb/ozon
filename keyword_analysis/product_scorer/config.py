"""
产品评分器配置
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# API 配置
# ──────────────────────────────────────────────

# DeepSeek 配置（用于 Ozon 决策引擎 - Layer 2）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v4"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# OpenAI 配置（用于 Vision 识别 - Layer 1，如果使用 GPT-4o）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_VISION_MODEL = "gpt-4o"  # 视觉识别专用

# 默认使用哪个 API 做视觉识别
# "openai" = 用 GPT-4o vision（更稳）
# "deepseek" = 用 DeepSeek V4 Pro vision（省钱）
VISION_PROVIDER = os.getenv("VISION_PROVIDER", "deepseek")

# ──────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR = ROOT_DIR / "data"

# ──────────────────────────────────────────────
# Ozon 运营参数（用于利润计算）
# ──────────────────────────────────────────────

OZON_COMMISSION_RATE = 0.15       # Ozon 佣金费率 15%
OZON_LOGISTICS_RATE_PER_KG = 350  # 每公斤物流费用（卢布）
OZON_MIN_LOGISTICS_RUB = 200      # 最低物流费（卢布）
RUSSIAN_DUTY_RATE = 0.05          # 俄罗斯关税 5%
EXCHANGE_RATE_CNY_RUB = 13.0      # 人民币兑卢布汇率
