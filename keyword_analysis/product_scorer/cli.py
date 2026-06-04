"""
CLI 入口 — Ozon 产品爆品评分系统（工业级 5 层架构）

用法:
  # 交互模式
  python -m keyword_analysis.product_scorer.cli

  # 命令行模式
  python -m keyword_analysis.product_scorer.cli \\
    --image path/to/product.jpg \\
    --price 1890 \\
    --cost 650 \\
    --weight 0.5

  # 纯文本模式（无图片）
  python -m keyword_analysis.product_scorer.cli \\
    --name "便携式咖啡机" \\
    --category "厨房电器" \\
    --price 2490 --cost 800 --weight 0.8

  # 指定视觉识别提供方
  python -m keyword_analysis.product_scorer.cli \\
    --image product.jpg --vision-provider openai
"""

import argparse
import sys
from pathlib import Path

from .models import ProductInput
from .layer4_pipeline import run_full_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="🚀 Ozon 产品爆品评分系统 — 5 层工业级 Prompt 工程架构",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --image ~/Desktop/product.jpg
  %(prog)s --name "自动猫砂盆" --price 4990 --cost 1500 --weight 3.2
  %(prog)s --image photo.png --price 990 --cost 300 --weight 0.2
        """,
    )

    # 产品信息
    parser.add_argument("--image", "-i", type=str, default="",
                        help="产品图片路径（支持 jpg/png/webp）")
    parser.add_argument("--name", "-n", type=str, default="",
                        help="产品名称（可选，留空由视觉识别自动填充）")
    parser.add_argument("--category", "-c", type=str, default="",
                        help="产品类目（可选）")

    # 价格信息
    parser.add_argument("--price", "-p", type=float, default=0.0,
                        help="Ozon 售价（卢布），如 1890")
    parser.add_argument("--cost", type=float, default=0.0,
                        help="产品成本（卢布，含采购+物流到俄罗斯仓）")
    parser.add_argument("--weight", "-w", type=float, default=0.0,
                        help="产品重量（kg），如 0.5")

    # 其他属性
    parser.add_argument("--dimensions", "-d", type=str, default="",
                        help="产品尺寸（如 30x20x15 cm）")
    parser.add_argument("--material", "-m", type=str, default="",
                        help="产品材质")

    # 系统配置
    parser.add_argument("--vision-provider", type=str,
                        choices=["deepseek", "openai"],
                        default=None,
                        help="视觉识别提供方（默认由 VISION_PROVIDER 环境变量决定）")
    parser.add_argument("--output-dir", "-o", type=str, default="",
                        help="报告输出目录（默认 output/）")

    return parser


def interactive_mode() -> ProductInput:
    """交互模式：逐步提示用户输入"""
    print("=" * 60)
    print("🚀 Ozon 产品爆品评分系统")
    print("   工业级 5 层 Prompt 工程架构")
    print("=" * 60)
    print("\n📝 请填写产品信息（留空可自动识别）:\n")

    image_path = input("  📸 产品图片路径（回车跳过）: ").strip().strip('"').strip("'")
    name = input("  📦 产品名称（回车自动识别）: ").strip()
    category = input("  🏷️  产品类目（回车自动识别）: ").strip()

    price_str = input("  💵 Ozon 售价（卢布，回车跳过）: ").strip()
    cost_str = input("  💰 产品成本（卢布，回车跳过）: ").strip()
    weight_str = input("  ⚖️  产品重量（kg，回车跳过）: ").strip()

    dimensions = input("  📐 产品尺寸（如 30x20x15cm，回车跳过）: ").strip()
    material = input("  🧪 产品材质（回车自动识别）: ").strip()

    return ProductInput(
        name=name,
        category=category,
        image_path=image_path,
        price_rub=float(price_str) if price_str else 0.0,
        cost_rub=float(cost_str) if cost_str else 0.0,
        weight_kg=float(weight_str) if weight_str else 0.0,
        dimensions=dimensions,
        material=material,
    )


def main():
    parser = build_parser()
    args = parser.parse_args()

    # 如果没有参数 → 交互模式
    if len(sys.argv) == 1:
        product = interactive_mode()
    else:
        product = ProductInput(
            name=args.name,
            category=args.category,
            image_path=args.image,
            price_rub=args.price,
            cost_rub=args.cost,
            weight_kg=args.weight,
            dimensions=args.dimensions,
            material=args.material,
        )

        # 如果指定了 vision provider
        if args.vision_provider:
            import os
            os.environ["VISION_PROVIDER"] = args.vision_provider

    # 校验：起码要有图片或名称
    if not product.image_path and not product.name:
        print("\n⚠️  请至少提供图片路径或产品名称")
        print("   使用 --help 查看用法")
        sys.exit(1)

    # 运行完整流水线
    result = run_full_pipeline(product, verbose=True)

    # 最终摘要
    summary = result["summary"]
    print(f"\n{'='*60}")
    print(f"✅ 流水线完成")
    print(f"   产品: {summary['product_name']}")
    print(f"   评分: {summary['total_score']}/100  ({summary['grade_cn']})")
    print(f"   结论: {summary['conclusion_cn']}")
    print(f"   报告: {result['layer_3_report_path']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
