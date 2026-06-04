import base64
import json
import os
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v4"
)


DEFAULT_AGENT_OUTPUT = {
    "scene_type": "",
    "camera": "",
    "lighting": "",
    "composition": "",
    "main_copy_ru": "",
    "secondary_copy_ru": "",
    "visual_focus": [],
    "negative_prompt": "",
    "generation_prompt": "",
}

VISUAL_AGENT_CONTRACT = (
    "Return JSON with these keys exactly when possible: scene_type, camera, lighting, "
    "composition, main_copy_ru, secondary_copy_ru, visual_focus, negative_prompt. "
    "The concept should be a dense Ozon-style marketplace creative with a bold Russian "
    "headline area, product-centered composition, multiple information elements, badges, "
    "benefit callouts, strong contrast, and clean zones for post-production text. "
    "Do not ask the image model to render final text directly. Keep the product identity, "
    "shape, color, material, proportions, brand mood, lighting language, and graphic style "
    "consistent with the shared suite_consistency guide."
)


@dataclass
class ProductInput:
    name: str
    category: str = ""
    image_path: str = ""
    dimensions: str = ""
    material: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


def load_product_image(product: ProductInput) -> dict[str, Any] | None:
    if not product.image_path:
        return None

    image_path = Path(product.image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Product image not found: {image_path}")

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/{image_path.suffix.lstrip('.')};base64,{encoded}"},
    }


def safe_json_loads(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def with_defaults(data: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = defaults.copy()
    for key, value in data.items():
        if value is not None:
            merged[key] = value
    if not isinstance(merged.get("visual_focus"), list):
        merged["visual_focus"] = []
    return merged


class BaseAgent:
    def __init__(self, role_name: str, system_prompt: str):
        self.role_name = role_name
        self.system_prompt = system_prompt

    def generate(self, product: ProductInput, context: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "product": asdict(product),
            "context": context or {},
        }
        user_content: list[dict[str, Any]] = [
            {"type": "text", "text": json.dumps(payload, ensure_ascii=False)}
        ]
        # DeepSeek V4 Pro supports vision input — include product image if available
        image_content = load_product_image(product)
        if image_content:
            user_content.append(image_content)

        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {
                    "role": "system",
                    "content": (
                        self.system_prompt
                        + "\nReturn valid JSON only. If a field is unknown, use an empty string or empty array."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
        return safe_json_loads(response.choices[0].message.content or "{}")


class SellingPointAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "SellingPointAgent",
            (
                "You are an Ozon marketplace product strategist. Analyze product name, category, "
                "dimensions, material, parameters, and image clues. Extract buyer-facing selling points, "
                "usage benefits, proof points, and Russian ecommerce wording. Return JSON with keys: "
                "core_selling_points, buyer_pains, proof_points, visual_priorities, tone_ru, forbidden_claims."
            ),
        )


class TextDesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "TextDesignAgent",
            (
                "You are a Russian ecommerce typography and layout director for Ozon gallery images. "
                "Design concise Russian copy, hierarchy, typography zones, label style, safe areas, and "
                "which image types should use text overlays. Return JSON with keys: text_system, "
                "main_copy_options_ru, secondary_copy_options_ru, label_style, placement_rules, no_text_scenes."
            ),
        )


class SuiteConsistencyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "SuiteConsistencyAgent",
            (
                "You are an art director responsible for visual consistency across a full Ozon product "
                "gallery. Create a strict consistency guide based on the product input and selling strategy. "
                "Return JSON with keys: product_identity, fixed_visual_traits, color_palette, background_style, "
                "lighting_style, camera_rules, graphic_system, recurring_badges, forbidden_variations. "
                "The guide must prevent the product from changing shape, color, material, size impression, "
                "or brand style between images."
            ),
        )


class MainInfographicAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "MainInfographicAgent",
            (
                "Ozon first-image creative director. Create a high-impact Russian marketplace poster "
                "concept similar to Ozon/WB listing covers: large product, oversized headline zone, "
                "quantity badge, bonus/gift badge when relevant, multiple commercial visual elements, "
                "and clear hierarchy. This is not an Amazon-style white-background image. "
                + VISUAL_AGENT_CONTRACT
            ),
        )


class DetailAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "DetailAgent",
            "Detail image expert for Ozon. Create macro product texture/detail image concepts. "
            + VISUAL_AGENT_CONTRACT,
        )


class DimensionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "DimensionAgent",
            (
                "Dimension infographic expert for Ozon. Create clear size and scale comparison image concepts. "
                "Use product.dimensions as the source of truth. Prefer visible measurement arrows, scale "
                "comparison, compact spec badges, and clear Russian labels. "
                + VISUAL_AGENT_CONTRACT
            ),
        )


class FeatureAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "FeatureAgent",
            "Feature infographic expert for Ozon. Create benefit-led product feature image concepts. "
            + VISUAL_AGENT_CONTRACT,
        )


class LifestyleAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "LifestyleAgent",
            "Lifestyle expert for Ozon. Create believable in-use product image concepts. "
            + VISUAL_AGENT_CONTRACT,
        )


class SceneDesignAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            "SceneDesignAgent",
            (
                "Scene design expert for Ozon. Create a premium contextual scene that matches the product "
                "category, buyer use case, material, and selling points. Focus on environment, props, mood, "
                "and realistic product placement. "
                + VISUAL_AGENT_CONTRACT
            ),
        )


def build_generation_prompt(agent_name: str, agent_output: dict[str, Any], strategy: dict[str, Any]) -> str:
    output = with_defaults(agent_output, DEFAULT_AGENT_OUTPUT)
    text_design = strategy.get("text_design", {})
    selling_points = strategy.get("selling_points", {})
    suite_consistency = strategy.get("suite_consistency", {})

    focus = ", ".join(output.get("visual_focus", []))
    priorities = ", ".join(selling_points.get("visual_priorities", []))
    prompt_parts = [
        "Create one image from a coherent Ozon product image suite.",
        "This image must look like it belongs to the same listing gallery as every other generated image.",
        f"SUITE CONSISTENCY GUIDE: {json.dumps(suite_consistency, ensure_ascii=False)}",
        "Keep the exact same product identity across the suite: same product shape, color, material, proportions, key details, and package/count impression.",
        "Use the same visual language across the suite: related palette, lighting, contrast, graphic badges, typography zones, and marketplace poster style.",
        "Only change the scene purpose required by the current image type; do not redesign the product.",
        output["scene_type"],
        output["composition"],
        output["camera"],
        output["lighting"],
        f"visual focus: {focus}" if focus else "",
        f"selling priorities: {priorities}" if priorities else "",
        "dense Ozon marketplace visual style, bold commercial composition, multiple information zones",
        "no embedded text in the generated image; leave clean areas for post-production text overlays",
        f"text layout guidance: {json.dumps(text_design.get('placement_rules', ''), ensure_ascii=False)}",
        f"image type: {agent_name}",
    ]
    prompt = ", ".join(part for part in prompt_parts if part)
    if output.get("negative_prompt"):
        prompt += (
            f" --negative {output['negative_prompt']}, inconsistent product, changed color, changed shape, "
            "changed material, wrong quantity, different brand style, mismatched background system, "
            "misspelled text, fake letters, watermark"
        )
    else:
        prompt += (
            " --negative inconsistent product, changed color, changed shape, changed material, wrong quantity, "
            "different brand style, mismatched background system, misspelled text, fake letters, watermark"
        )
    return prompt


def generate_image(prompt: str, output_path: Path, product: ProductInput) -> Path:
    """
    Generate a product image using DeepSeek V4 Pro for prompt enrichment,
    then save a placeholder image (DeepSeek doesn't yet offer native image generation).

    Note: When DeepSeek releases image generation support, replace the placeholder
    logic with the actual image API call.
    """
    # Use DeepSeek V4 Pro to refine / enrich the image prompt
    enrichment_response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert image prompt engineer. Given a product description and "
                    "visual concept, produce a single, detailed, highly specific English prompt "
                    "for an AI image generator. Focus on lighting, composition, color palette, "
                    "product placement, background, and mood. Return only the prompt text, no JSON."
                ),
            },
            {
                "role": "user",
                "content": f"Product: {product.name}, Category: {product.category}. "
                           f"Original concept: {prompt}",
            },
        ],
        temperature=0.7,
    )
    enriched_prompt = enrichment_response.choices[0].message.content or prompt

    # Save enriched prompt alongside the image for reference
    prompt_path = output_path.with_suffix(".txt")
    prompt_path.write_text(enriched_prompt, encoding="utf-8")

    # Create a placeholder image (DeepSeek doesn't currently support image generation)
    # Replace this block when an image generation API becomes available
    img = Image.new("RGB", (1024, 1024), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)
    draw.text((512, 512), f"[{product.name}]\nImage prompt generated by\ndeepseek-v4-pro", fill=(60, 60, 60), anchor="mm")
    img.save(output_path)

    return output_path


def font_or_default(size: int = 36) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def post_process_image(image_path: Path, agent_name: str, agent_output: dict[str, Any], strategy: dict[str, Any]) -> Path:
    text_design = strategy.get("text_design", {})
    no_text_scenes = set(text_design.get("no_text_scenes", []))
    if agent_name in no_text_scenes:
        return image_path

    output = with_defaults(agent_output, DEFAULT_AGENT_OUTPUT)
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    title_font = font_or_default(44)
    subtitle_font = font_or_default(28)

    main_copy = output.get("main_copy_ru") or first_text(text_design.get("main_copy_options_ru"))
    secondary_copy = output.get("secondary_copy_ru") or first_text(text_design.get("secondary_copy_options_ru"))

    render_title_panel(draw, img, main_copy, secondary_copy, title_font, subtitle_font)

    if agent_name == "DimensionAgent":
        render_dimension_overlay(draw, img, strategy, title_font, subtitle_font)

    processed_path = image_path.with_name(f"{image_path.stem}_post.png")
    img.save(processed_path)
    return processed_path


def render_title_panel(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    main_copy: str,
    secondary_copy: str,
    title_font: ImageFont.ImageFont,
    subtitle_font: ImageFont.ImageFont,
) -> None:
    margin = 48
    panel_height = 150
    draw.rounded_rectangle(
        (margin - 18, margin - 18, img.width - margin + 18, margin + panel_height),
        radius=20,
        fill=(255, 255, 255),
        outline=(225, 225, 225),
        width=2,
    )
    if main_copy:
        draw.text((margin, margin), main_copy, fill=(28, 28, 28), font=title_font)
    if secondary_copy:
        draw.text((margin, margin + 62), secondary_copy, fill=(75, 75, 75), font=subtitle_font)


def render_dimension_overlay(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    strategy: dict[str, Any],
    title_font: ImageFont.ImageFont,
    subtitle_font: ImageFont.ImageFont,
) -> None:
    product = strategy.get("product", {})
    dimensions = product.get("dimensions") or "\u0443\u0442\u043e\u0447\u043d\u0438\u0442\u0435 \u0440\u0430\u0437\u043c\u0435\u0440"
    material = product.get("material") or ""

    accent = (238, 32, 38)
    dark = (24, 24, 24)
    yellow = (255, 222, 35)
    white = (255, 255, 255)

    badge_box = (56, img.height - 250, 430, img.height - 64)
    draw.rounded_rectangle(badge_box, radius=28, fill=dark, outline=yellow, width=5)
    draw.text((86, img.height - 226), "\u0420\u0410\u0417\u041c\u0415\u0420", fill=yellow, font=title_font)
    draw.text((86, img.height - 162), dimensions, fill=white, font=subtitle_font)
    if material:
        draw.text((86, img.height - 118), material.upper(), fill=(210, 210, 210), font=subtitle_font)

    x1, x2 = 475, img.width - 95
    y = img.height - 150
    draw.line((x1, y, x2, y), fill=accent, width=7)
    draw.polygon([(x1, y), (x1 + 34, y - 18), (x1 + 34, y + 18)], fill=accent)
    draw.polygon([(x2, y), (x2 - 34, y - 18), (x2 - 34, y + 18)], fill=accent)
    draw.rounded_rectangle((x1 + 64, y - 78, x2 - 56, y - 26), radius=18, fill=white)
    draw.text(
        (x1 + 88, y - 76),
        "\u0422\u041e\u0427\u041d\u042b\u0415 \u0413\u0410\u0411\u0410\u0420\u0418\u0422\u042b",
        fill=accent,
        font=subtitle_font,
    )

    vertical_x = img.width - 88
    y1, y2 = 250, img.height - 285
    draw.line((vertical_x, y1, vertical_x, y2), fill=accent, width=7)
    draw.polygon([(vertical_x, y1), (vertical_x - 18, y1 + 34), (vertical_x + 18, y1 + 34)], fill=accent)
    draw.polygon([(vertical_x, y2), (vertical_x - 18, y2 - 34), (vertical_x + 18, y2 - 34)], fill=accent)


def first_text(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    if isinstance(value, str):
        return value
    return ""


def generate_suite(product: ProductInput, output_root: Path) -> dict[str, Any]:
    product_folder = output_root / safe_folder_name(product.name)
    product_folder.mkdir(parents=True, exist_ok=True)

    selling_points = SellingPointAgent().generate(product)
    text_design = TextDesignAgent().generate(product, {"selling_points": selling_points})
    suite_consistency = SuiteConsistencyAgent().generate(
        product,
        {
            "selling_points": selling_points,
            "text_design": text_design,
        },
    )
    strategy = {
        "product": asdict(product),
        "selling_points": selling_points,
        "text_design": text_design,
        "suite_consistency": suite_consistency,
    }

    visual_agents = [
        MainInfographicAgent(),
        DetailAgent(),
        DimensionAgent(),
        FeatureAgent(),
        LifestyleAgent(),
        SceneDesignAgent(),
    ]

    result = {
        "input": asdict(product),
        "strategy": strategy,
        "images": {},
    }

    for agent in visual_agents:
        agent_output = with_defaults(agent.generate(product, strategy), DEFAULT_AGENT_OUTPUT)
        agent_output["generation_prompt"] = build_generation_prompt(agent.role_name, agent_output, strategy)

        raw_path = product_folder / f"{agent.role_name}.png"
        generate_image(agent_output["generation_prompt"], raw_path, product)
        final_path = post_process_image(raw_path, agent.role_name, agent_output, strategy)

        agent_output["image_path"] = str(final_path)
        result["images"][agent.role_name] = agent_output

    return result


def safe_folder_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in value).strip("_")


if __name__ == "__main__":
    products = [
        ProductInput(
            name="Ice Pack (Cooling Gel)",
            category="Reusable cooling pack",
            image_path="",
            dimensions="18 x 10 x 2 cm",
            material="gel, plastic shell",
            parameters={"use_case": "cold therapy, lunch bag, outdoor travel"},
        ),
        ProductInput(
            name="Highland Cow Figurine",
            category="Home decor figurine",
            image_path="",
            dimensions="12 x 8 x 10 cm",
            material="resin",
            parameters={"style": "cute Nordic desk decor"},
        ),
    ]

    output_root = Path("outputs")
    output_root.mkdir(exist_ok=True)
    results = {}

    for product in products:
        results[product.name] = generate_suite(product, output_root)

    with (output_root / "full_pipeline.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Ozon suite pipeline complete: strategy + 6 image types + JSON output")
