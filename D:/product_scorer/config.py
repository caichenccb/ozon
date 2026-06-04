"""
产品评分器配置
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# API 配置
# ──────────────────────────────────────────────

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v4"
DEEPSEEK_MODEL = "deepseek-v4-pro"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_VISION_MODEL = "gpt-4o"

VISION_PROVIDER = os.getenv("VISION_PROVIDER", "deepseek")

# ──────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR = ROOT_DIR / "data"

# ──────────────────────────────────────────────
# Ozon 运营参数
# ──────────────────────────────────────────────

OZON_COMMISSION_RATE = 0.15
OZON_LOGISTICS_RATE_PER_KG = 350
OZON_MIN_LOGISTICS_RUB = 200
RUSSIAN_DUTY_RATE = 0.05
EXCHANGE_RATE_CNY_RUB = 13.0
