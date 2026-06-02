SELLER_CONSTRAINTS = {
    "cross_border": True,
    "shipping_days": 30,

    "min_price_rub": 2000,

    "avoid_categories": [
        "clothing",
        "shoes",
        "electronic_parts",
        "liquid"
    ],

    "weights": {
        "demand": 0.30,
        "profit": 0.30,
        "cross_border": 0.25,
        "competition": 0.15
    }
}