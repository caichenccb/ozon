#!/usr/bin/env python3
"""
🚀 Ozon 产品爆品评分系统 — 根目录快捷入口

用法:
  python ozon_scorer.py
  python ozon_scorer.py --image path/to/product.jpg --price 1890 --cost 650
  python ozon_scorer.py --name "便携式咖啡机" --price 2490 --cost 800
"""

import sys
from pathlib import Path

# 确保能找到模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from keyword_analysis.product_scorer.cli import main

if __name__ == "__main__":
    main()
