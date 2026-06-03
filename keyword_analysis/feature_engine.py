"""
特征工程模块 - 代理引用

重要:
  原 calculate_market_features、_safe_get、_normalize_score 已移至
  scoring_engine 模块，此处仅保留向后兼容的引用。

  新代码应直接导入 scoring_engine:
    from scoring_engine import calculate_market_features, compute_full_score
"""

from scoring_engine import calculate_market_features, _safe_get, _normalize_score

__all__ = ["calculate_market_features", "_safe_get", "_normalize_score"]