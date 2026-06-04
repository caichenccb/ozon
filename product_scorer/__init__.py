"""
Ozon 产品爆品评分系统
=====================
工业级 5 层 Prompt 工程架构：

  Layer 1: Vision Prompt  — 视觉识别（GPT-4o / DeepSeek V4 Pro Vision）
  Layer 2: Ozon 决策引擎  — 选品商业判断（DeepSeek V4 Pro）
  Layer 3: 标准输出格式    — 强制统一的结构化报告
  Layer 4: 系统拼接逻辑    — 完整链路编排
  Layer 5: 工程优化        — 防幻觉、强制 JSON、Ozon 专用规则

用法:
  python -m product_scorer.cli --image path/to/product.jpg
"""

__version__ = "2.0.0"
