#!/usr/bin/env python3
"""
🚀 Ozon 产品爆品评分系统 — 快捷入口

用法:
  python run.py
  python run.py --image path/to/product.jpg --price 1890 --cost 650
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from product_scorer.cli import main

if __name__ == "__main__":
    main()
