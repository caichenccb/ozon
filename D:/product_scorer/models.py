"""数据模型 — 产品评分系统的所有数据结构"""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class VisualFeatures:
    shape: str = ""
    color: str = ""
    material_guess: str = ""
    size_relation: str = ""


@dataclass
class VisionOutput:
    product_name: str = ""
    category: str = ""
    sub_category: str = ""
    visual_features: VisualFeatures = field(default_factory=VisualFeatures)
    components: list[str] = field(default_factory=list)
    visible_functions: list[str] = field(default_factory=list)
    usage_scene: str = ""
    possible_users: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "product_name": self.product_name,
            "category": self.category,
            "sub_category": self.sub_category,
            "visual_features": asdict(self.visual_features),
            "components": self.components,
            "visible_functions": self.visible_functions,
            "usage_scene": self.usage_scene,
            "possible_users": self.possible_users,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisionOutput":
        vf_data = data.get("visual_features", {})
        if isinstance(vf_data, dict):
            visual_features = VisualFeatures(
                shape=vf_data.get("shape", ""),
                color=vf_data.get("color", ""),
                material_guess=vf_data.get("material_guess", ""),
                size_relation=vf_data.get("size_relation", ""),
            )
        else:
            visual_features = VisualFeatures()
        return cls(
            product_name=data.get("product_name", ""),
            category=data.get("category", ""),
            sub_category=data.get("sub_category", ""),
            visual_features=visual_features,
            components=data.get("components", []),
            visible_functions=data.get("visible_functions", []),
            usage_scene=data.get("usage_scene", ""),
            possible_users=data.get("possible_users", []),
            confidence=float(data.get("confidence", 0.0)),
        )


@dataclass
class MarketAnalysis:
    category_trend: str = ""
    demand_nature: str = ""
    structural_opportunity: str = ""
    missing_info: list[str] = field(default_factory=list)


@dataclass
class ProductPositioning:
    target_users: str = ""
    use_scenarios: str = ""
    buying_motivation: str = ""
    alternatives: str = ""


@dataclass
class CompetitionAnalysis:
    mainstream_tactics: str = ""
    homogenization_level: str = ""
    entry_points: list[str] = field(default_factory=list)
    key_to_win: str = ""


@dataclass
class OzonFitAnalysis:
    search_keywords_ru: list[str] = field(default_factory=list)
    traffic_structure: str = ""
    conversion_strategy: str = ""
    ad_suitable: bool = True


@dataclass
class Scores:
    market_demand: float = 0.0
    profit_margin: float = 0.0
    competition_ease: float = 0.0
    differentiation: float = 0.0
    conversion_potential: float = 0.0
    total: float = 0.0

    def calculate_total(self) -> float:
        self.total = round(
            self.market_demand + self.profit_margin + self.competition_ease
            + self.differentiation + self.conversion_potential, 1
        )
        return self.total

    def grade(self) -> str:
        if self.total >= 80: return "strong_hit"
        elif self.total >= 60: return "test_waters"
        elif self.total >= 40: return "cautious"
        else: return "not_recommended"

    def grade_cn(self) -> str:
        return {"strong_hit": "🔥 强爆品", "test_waters": "🧪 可试水",
                "cautious": "⚠️ 谨慎进入", "not_recommended": "❌ 不建议做"}.get(self.grade(), "未知")


@dataclass
class Verdict:
    conclusion: str = ""
    conclusion_cn: str = ""
    core_reason: str = ""
    scale_decision: str = ""


@dataclass
class DecisionOutput:
    market_analysis: MarketAnalysis = field(default_factory=MarketAnalysis)
    product_positioning: ProductPositioning = field(default_factory=ProductPositioning)
    competition_analysis: CompetitionAnalysis = field(default_factory=CompetitionAnalysis)
    ozon_fit_analysis: OzonFitAnalysis = field(default_factory=OzonFitAnalysis)
    scores: Scores = field(default_factory=Scores)
    verdict: Verdict = field(default_factory=Verdict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "market_analysis": {"category_trend": self.market_analysis.category_trend, "demand_nature": self.market_analysis.demand_nature, "structural_opportunity": self.market_analysis.structural_opportunity, "missing_info": self.market_analysis.missing_info},
            "product_positioning": {"target_users": self.product_positioning.target_users, "use_scenarios": self.product_positioning.use_scenarios, "buying_motivation": self.product_positioning.buying_motivation, "alternatives": self.product_positioning.alternatives},
            "competition_analysis": {"mainstream_tactics": self.competition_analysis.mainstream_tactics, "homogenization_level": self.competition_analysis.homogenization_level, "entry_points": self.competition_analysis.entry_points, "key_to_win": self.competition_analysis.key_to_win},
            "ozon_fit_analysis": {"search_keywords_ru": self.ozon_fit_analysis.search_keywords_ru, "traffic_structure": self.ozon_fit_analysis.traffic_structure, "conversion_strategy": self.ozon_fit_analysis.conversion_strategy, "ad_suitable": self.ozon_fit_analysis.ad_suitable},
            "scores": {"market_demand": self.scores.market_demand, "profit_margin": self.scores.profit_margin, "competition_ease": self.scores.competition_ease, "differentiation": self.scores.differentiation, "conversion_potential": self.scores.conversion_potential, "total": self.scores.total},
            "verdict": {"conclusion": self.verdict.conclusion, "conclusion_cn": self.verdict.conclusion_cn, "core_reason": self.verdict.core_reason, "scale_decision": self.verdict.scale_decision},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DecisionOutput":
        ma = data.get("market_analysis", {})
        pp = data.get("product_positioning", {})
        ca = data.get("competition_analysis", {})
        of = data.get("ozon_fit_analysis", {})
        sc = data.get("scores", {})
        ve = data.get("verdict", {})
        return cls(
            market_analysis=MarketAnalysis(category_trend=ma.get("category_trend",""), demand_nature=ma.get("demand_nature",""), structural_opportunity=ma.get("structural_opportunity",""), missing_info=ma.get("missing_info",[])),
            product_positioning=ProductPositioning(target_users=pp.get("target_users",""), use_scenarios=pp.get("use_scenarios",""), buying_motivation=pp.get("buying_motivation",""), alternatives=pp.get("alternatives","")),
            competition_analysis=CompetitionAnalysis(mainstream_tactics=ca.get("mainstream_tactics",""), homogenization_level=ca.get("homogenization_level",""), entry_points=ca.get("entry_points",[]), key_to_win=ca.get("key_to_win","")),
            ozon_fit_analysis=OzonFitAnalysis(search_keywords_ru=of.get("search_keywords_ru",[]), traffic_structure=of.get("traffic_structure",""), conversion_strategy=of.get("conversion_strategy",""), ad_suitable=of.get("ad_suitable",True)),
            scores=Scores(market_demand=float(sc.get("market_demand",0)), profit_margin=float(sc.get("profit_margin",0)), competition_ease=float(sc.get("competition_ease",0)), differentiation=float(sc.get("differentiation",0)), conversion_potential=float(sc.get("conversion_potential",0)), total=float(sc.get("total",0))),
            verdict=Verdict(conclusion=ve.get("conclusion",""), conclusion_cn=ve.get("conclusion_cn",""), core_reason=ve.get("core_reason",""), scale_decision=ve.get("scale_decision","")),
        )


@dataclass
class ProductInput:
    name: str = ""
    category: str = ""
    image_path: str = ""
    dimensions: str = ""
    material: str = ""
    price_rub: float = 0.0
    cost_rub: float = 0.0
    weight_kg: float = 0.0
    parameters: dict[str, Any] = field(default_factory=dict)
